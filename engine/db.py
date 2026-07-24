import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
from typing import List, Dict, Any

# PostgreSQL Database Configuration
DB_HOST = "localhost"
DB_NAME = "duit_ledger"
DB_USER = "thermo_user"
DB_PASS = "DuitSecurePass99"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def init_db():
    """Initializes PostgreSQL database tables for blocks, transactions, and validators if they do not exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create blocks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blocks (
        height INTEGER PRIMARY KEY,
        timestamp DOUBLE PRECISION,
        settled_entropy VARCHAR(66),
        lattice_energy_state DOUBLE PRECISION,
        delta_entropy DOUBLE PRECISION,
        validator VARCHAR(42),
        winning_bot VARCHAR(50),
        bot_saving_pct DOUBLE PRECISION
    )
    """)
    
    # 2. Create transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        tx_id VARCHAR(66) PRIMARY KEY,
        block_height INTEGER REFERENCES blocks(height) ON DELETE CASCADE,
        sender VARCHAR(42),
        recipient VARCHAR(42),
        amount_joules BIGINT,
        entropy_salt VARCHAR(66),
        target_energy_state VARCHAR(20),
        timestamp DOUBLE PRECISION
    )
    """)
    
    # 3. Create validators table (Staking & Node Registry)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS validators (
        address VARCHAR(42) PRIMARY KEY,
        name VARCHAR(50),
        stake_amount_joules BIGINT,
        tier_type VARCHAR(10),
        status VARCHAR(20),
        cooldown_until DOUBLE PRECISION
    )
    """)
    
    conn.commit()
    conn.close()

def save_block_to_db(block: Dict[str, Any]):
    """Saves a block and all its transactions to PostgreSQL in a single database transaction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert Block
        cursor.execute("""
        INSERT INTO blocks 
        (height, timestamp, settled_entropy, lattice_energy_state, delta_entropy, validator, winning_bot, bot_saving_pct)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (height) DO UPDATE SET
            timestamp = EXCLUDED.timestamp,
            settled_entropy = EXCLUDED.settled_entropy,
            lattice_energy_state = EXCLUDED.lattice_energy_state,
            delta_entropy = EXCLUDED.delta_entropy,
            validator = EXCLUDED.validator,
            winning_bot = EXCLUDED.winning_bot,
            bot_saving_pct = EXCLUDED.bot_saving_pct
        """, (
            block["block_height"],
            block["timestamp"],
            block["settled_entropy"],
            block["lattice_energy_state"],
            block["delta_entropy"],
            block["validator"],
            block.get("winning_bot"),
            block.get("bot_saving_pct", 0.0)
        ))
        
        # Insert Transactions
        for tx in block.get("transactions", []):
            cursor.execute("""
            INSERT INTO transactions
            (tx_id, block_height, sender, recipient, amount_joules, entropy_salt, target_energy_state, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tx_id) DO UPDATE SET
                block_height = EXCLUDED.block_height,
                sender = EXCLUDED.sender,
                recipient = EXCLUDED.recipient,
                amount_joules = EXCLUDED.amount_joules,
                entropy_salt = EXCLUDED.entropy_salt,
                target_energy_state = EXCLUDED.target_energy_state,
                timestamp = EXCLUDED.timestamp
            """, (
                tx["tx_id"],
                block["block_height"],
                tx["sender"],
                tx["recipient"],
                tx["amount_joules"],
                tx["entropy_salt"],
                tx["target_energy_state"],
                tx.get("timestamp", time.time())
            ))
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def load_blocks_from_db() -> List[Dict[str, Any]]:
    """Loads all blocks and their nested transactions from PostgreSQL, ordered by height"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM blocks ORDER BY height ASC")
    block_rows = cursor.fetchall()
    
    blocks = []
    for row in block_rows:
        block = dict(row)
        block["block_height"] = block.pop("height")
        
        cursor.execute("SELECT * FROM transactions WHERE block_height = %s", (block["block_height"],))
        tx_rows = cursor.fetchall()
        
        txs = []
        for tx_row in tx_rows:
            tx = dict(tx_row)
            txs.append(tx)
            
        block["transactions"] = txs
        blocks.append(block)
        
    conn.close()
    return blocks

def get_block_by_height(height: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM blocks WHERE height = %s", (height,))
    row = cursor.fetchone()
    block = None
    if row:
        block = dict(row)
        block["block_height"] = block.pop("height")
        cursor.execute("SELECT * FROM transactions WHERE block_height = %s", (block["block_height"],))
        block["transactions"] = [dict(tx) for tx in cursor.fetchall()]
    conn.close()
    return block

def get_block_by_hash(entropy_hash: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM blocks WHERE settled_entropy = %s", (entropy_hash,))
    row = cursor.fetchone()
    block = None
    if row:
        block = dict(row)
        block["block_height"] = block.pop("height")
        cursor.execute("SELECT * FROM transactions WHERE block_height = %s", (block["block_height"],))
        block["transactions"] = [dict(tx) for tx in cursor.fetchall()]
    conn.close()
    return block

def get_transaction_by_id(tx_id: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM transactions WHERE tx_id = %s", (tx_id,))
    row = cursor.fetchone()
    tx = dict(row) if row else None
    conn.close()
    return tx

def get_transactions_by_address(address: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
    SELECT * FROM transactions 
    WHERE sender = %s OR recipient = %s 
    ORDER BY timestamp DESC
    """, (address, address))
    rows = cursor.fetchall()
    txs = [dict(r) for r in rows]
    conn.close()
    return txs

# Validator / Staking Helper Functions
def save_validator_to_db(val: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO validators (address, name, stake_amount_joules, tier_type, status, cooldown_until)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (address) DO UPDATE SET
        name = EXCLUDED.name,
        stake_amount_joules = EXCLUDED.stake_amount_joules,
        tier_type = EXCLUDED.tier_type,
        status = EXCLUDED.status,
        cooldown_until = EXCLUDED.cooldown_until
    """, (
        val["address"],
        val["name"],
        val["stake_amount_joules"],
        val["tier_type"],
        val["status"],
        val["cooldown_until"]
    ))
    conn.commit()
    conn.close()

def load_validators_from_db() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM validators")
    rows = cursor.fetchall()
    validators = [dict(r) for r in rows]
    conn.close()
    return validators

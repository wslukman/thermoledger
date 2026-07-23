import sqlite3
import os
import time
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "duit_chain.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database tables for blocks and transactions if they do not exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create blocks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blocks (
        height INTEGER PRIMARY KEY,
        timestamp REAL,
        settled_entropy TEXT,
        lattice_energy_state REAL,
        delta_entropy REAL,
        validator TEXT,
        winning_bot TEXT,
        bot_saving_pct REAL
    )
    """)
    
    # 2. Create transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        tx_id TEXT PRIMARY KEY,
        block_height INTEGER,
        sender TEXT,
        recipient TEXT,
        amount_joules INTEGER,
        entropy_salt TEXT,
        target_energy_state TEXT,
        timestamp REAL,
        FOREIGN KEY(block_height) REFERENCES blocks(height)
    )
    """)
    
    conn.commit()
    conn.close()

def save_block_to_db(block: Dict[str, Any]):
    """Saves a block and all its transactions to SQLite in a single commit transaction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert Block
        cursor.execute("""
        INSERT OR REPLACE INTO blocks 
        (height, timestamp, settled_entropy, lattice_energy_state, delta_entropy, validator, winning_bot, bot_saving_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            INSERT OR REPLACE INTO transactions
            (tx_id, block_height, sender, recipient, amount_joules, entropy_salt, target_energy_state, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    """Loads all blocks and their nested transactions from SQLite, ordered by height"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM blocks ORDER BY height ASC")
    block_rows = cursor.fetchall()
    
    blocks = []
    for row in block_rows:
        block = dict(row)
        
        # Rename row keys to match memory representation
        block["block_height"] = block.pop("height")
        
        # Fetch transactions for this block
        cursor.execute("SELECT * FROM transactions WHERE block_height = ?", (block["block_height"],))
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
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blocks WHERE height = ?", (height,))
    row = cursor.fetchone()
    block = None
    if row:
        block = dict(row)
        block["block_height"] = block.pop("height")
        cursor.execute("SELECT * FROM transactions WHERE block_height = ?", (block["block_height"],))
        block["transactions"] = [dict(tx) for tx in cursor.fetchall()]
    conn.close()
    return block

def get_block_by_hash(entropy_hash: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blocks WHERE settled_entropy = ?", (entropy_hash,))
    row = cursor.fetchone()
    block = None
    if row:
        block = dict(row)
        block["block_height"] = block.pop("height")
        cursor.execute("SELECT * FROM transactions WHERE block_height = ?", (block["block_height"],))
        block["transactions"] = [dict(tx) for tx in cursor.fetchall()]
    conn.close()
    return block

def get_transaction_by_id(tx_id: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE tx_id = ?", (tx_id,))
    row = cursor.fetchone()
    tx = dict(row) if row else None
    conn.close()
    return tx

def get_transactions_by_address(address: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM transactions 
    WHERE sender = ? OR recipient = ? 
    ORDER BY timestamp DESC
    """, (address, address))
    rows = cursor.fetchall()
    txs = [dict(r) for r in rows]
    conn.close()
    return txs

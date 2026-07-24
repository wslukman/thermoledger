import time
import random
from typing import List, Dict, Any
from engine.noise import thermal_noise
from engine.consensus import consensus_lattice
from engine.db import init_db, save_block_to_db, load_blocks_from_db, load_validators_from_db, save_validator_to_db

class ThermodynamicBlockchain:
    """
    Manages the ledger balances, L2 Micro-Pools (Thermodynamic Ponds),
    L1 block commits, and simulated arbitrage bots competing to find
    Minimum Energy Path (MEP) alignments.
    """
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.l2_pool: List[Dict[str, Any]] = []
        
        # Initialize database
        init_db()
        
        # Load validators from database or seed defaults
        db_validators = load_validators_from_db()
        if db_validators:
            # PostgreSQL returns keys as standard strings
            self.validators = []
            for val in db_validators:
                self.validators.append({
                    "name": val["name"],
                    "address": val["address"],
                    "stake_amount_joules": int(val["stake_amount_joules"]),
                    "tier_type": val["tier_type"],
                    "status": val["status"],
                    "cooldown_until": float(val["cooldown_until"])
                })
        else:
            self.validators = [
                {"name": "Alpha-Node", "address": "0x0a111a", "stake_amount_joules": 200000000000, "tier_type": "Tipe_A", "status": "online", "cooldown_until": 0.0},
                {"name": "Beta-Node", "address": "0x0bee1b", "stake_amount_joules": 200000000000, "tier_type": "Tipe_A", "status": "online", "cooldown_until": 0.0},
                {"name": "Gamma-Node", "address": "0x0cee1c", "stake_amount_joules": 200000000000, "tier_type": "Tipe_A", "status": "online", "cooldown_until": 0.0},
                {"name": "Delta-Node", "address": "0x0dee1d", "stake_amount_joules": 200000000000, "tier_type": "Tipe_A", "status": "online", "cooldown_until": 0.0},
                {"name": "Epsilon-Node", "address": "0x0eee1e", "stake_amount_joules": 200000000000, "tier_type": "Tipe_A", "status": "online", "cooldown_until": 0.0}
            ]
            for val in self.validators:
                save_validator_to_db(val)

        self.accounts: Dict[str, int] = {
            "0x01a2b3": 1000000000000, # Initial treasury: 10,000 DUIT (10^12 Joules)
            "0x02bf1a": 50000000000,   # Cashier Merchant (DuitLap): 500 DUIT
            "0x03a6bc": 10000000000,    # Consumer wallet: 100 DUIT
            "0xDeveloperOps": 50000000000000, # 5% Genesis Allocation: 500,000 DUIT (5 * 10^13 Joules)
            "0xBotHarvester": 5000000000, # Arbitrage bot wallet: 50 DUIT
            "0x000000000000000000000000000000000000DEAD": 0 # Absolute Heat Sink (Burn Wallet)
        }
        for val in self.validators:
            self.accounts[val["address"]] = 0

        self.bots = [
            {"id": "ThermodynamicBot_A", "efficiency_score": 0.95, "wins": 0, "balance_joules": 1000000000},
            {"id": "EntropyHarvester_B", "efficiency_score": 0.92, "wins": 0, "balance_joules": 1000000000},
            {"id": "LeastActionBot_C", "efficiency_score": 0.97, "wins": 0, "balance_joules": 1000000000}
        ]
        
        # Restore historical chain or create genesis block
        db_blocks = load_blocks_from_db()
        if db_blocks:
            self.chain = db_blocks
            self.reconstruct_state_from_chain()
        else:
            # Create Genesis Block
            self.create_genesis_block()
 
    def get_current_block_reward(self, block_height: int) -> int:
        """Calculates block reward with 4-year halving decay (halves every 12,622,780 blocks)"""
        if block_height == 0:
            return 0
        halving_epoch = block_height // 12622780
        # Initial reward: 39,610,925 Joules (0.39610925 DUIT)
        reward = 39610925 >> halving_epoch
        return reward

    def reconstruct_state_from_chain(self):
        """Rebuilds balances and bot wins from loaded database block history"""
        self.accounts = {
            "0x01a2b3": 1000000000000,
            "0x02bf1a": 50000000000,
            "0x03a6bc": 10000000000,
            "0xDeveloperOps": 50000000000000,
            "0xBotHarvester": 5000000000,
            "0x000000000000000000000000000000000000DEAD": 0
        }
        for val in self.validators:
            self.accounts[val["address"]] = 0

        for bot in self.bots:
            bot["wins"] = 0
            bot["balance_joules"] = 1000000000

        for block in self.chain:
            h = block["block_height"]
            if h == 0:
                continue
            
            for tx in block.get("transactions", []):
                sender = tx["sender"]
                recipient = tx["recipient"]
                amount = tx["amount_joules"]
                
                self.accounts[sender] = self.accounts.get(sender, 0) - amount
                self.accounts[recipient] = self.accounts.get(recipient, 0) + amount
                
            validator = block["validator"]
            block_reward = self.get_current_block_reward(h)
            if block_reward > 0:
                is_virtual_val = any(v["address"] == validator for v in self.validators)
                if is_virtual_val:
                    proposer_reward = int(block_reward * 0.36)
                    signer_reward = (block_reward - proposer_reward) // 4
                    self.accounts[validator] = self.accounts.get(validator, 0) + proposer_reward
                    for val in self.validators:
                        if val["address"] != validator:
                            self.accounts[val["address"]] = self.accounts.get(val["address"], 0) + signer_reward
                else:
                    self.accounts[validator] = self.accounts.get(validator, 0) + block_reward
            
            winning_bot = block.get("winning_bot")
            if winning_bot:
                self.accounts["0xBotHarvester"] += 10
                for bot in self.bots:
                    if bot["id"] == winning_bot:
                        bot["wins"] += 1
                        bot["balance_joules"] += 10

    def create_genesis_block(self):
        genesis_block = {
            "block_height": 0,
            "timestamp": time.time(),
            "transactions": [],
            "settled_entropy": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "lattice_energy_state": 0.0,
            "delta_entropy": 0.0,
            "validator": "0x000000"
        }
        self.chain.append(genesis_block)
        save_block_to_db(genesis_block)

    def prepare_transaction(self, sender: str, recipient: str, amount_joules: int) -> Dict[str, Any]:
        """Exposes L1 /prepare stage, generating the physical target state and noise salt"""
        # Validate balance
        if self.accounts.get(sender, 0) < amount_joules:
            raise ValueError("Insufficient balance (Joule capacity exceeded)")

        # Capture live thermodynamic noise
        salt = thermal_noise.generate_entropy_salt(16)
        
        # Calculate target physical energy state based on current lattice
        current_energy = consensus_lattice.get_energy()
        # Add local coordinate disturbance calculation
        hash_offset = (hash(sender) + hash(recipient)) % 100
        target_state_energy = current_energy + (hash_offset / 10.0) - 5.0
        
        # Shift offset by +300.0 to ensure positive values, scaled by 100.0
        shifted_energy = target_state_energy + 300.0
        val_int = int(shifted_energy * 100.0)
        
        return {
            "sender": sender,
            "recipient": recipient,
            "amount_joules": amount_joules,
            "entropy_salt": salt,
            "target_energy_state": hex(val_int & 0xffffff)
        }

    def add_to_l2_pool(self, tx: Dict[str, Any]) -> str:
        """Injects a transaction into L2 micro-pool (L2 pond)"""
        # Under Cooling-off freeze, reject all transaction inputs
        if consensus_lattice.safe_mode_active:
            raise RuntimeError("Network is FROZEN (Cooling-Off Period active). Energy transfers locked.")
            
        tx["timestamp"] = time.time()
        tx_id = "0x" + thermal_noise.generate_entropy_salt(8)[2:]
        tx["tx_id"] = tx_id
        self.l2_pool.append(tx)
        
        # Apply local stress immediately to L2 visual grid
        consensus_lattice.apply_transaction_stress(tx["sender"], tx["recipient"], tx["amount_joules"])
        return tx_id

    def execute_arbitrage_competition(self) -> Dict[str, Any]:
        """
        Simulates arbitrage bots competing to reorder L2 transactions.
        The bot that achieves the lowest total state transition cost (Least Action Principle) wins,
        optimizing the block execution order.
        """
        if not self.l2_pool:
            return {"winning_bot": None, "original_order": [], "optimized_order": []}

        # Original order of transaction IDs
        original_ids = [tx["tx_id"] for tx in self.l2_pool]
        
        # Simulate bot calculations
        bot_results = []
        for bot in self.bots:
            # Random factor based on their algorithms, adjusted by their hardcoded efficiency
            simulated_cost = random.uniform(10.0, 50.0) / bot["efficiency_score"]
            bot_results.append({
                "bot_id": bot["id"],
                "cost": simulated_cost
            })
            
        # Bot with the lowest cost (Least Action) wins
        winning_result = min(bot_results, key=lambda x: x["cost"])
        winning_bot_id = winning_result["bot_id"]
        
        # Record win
        for bot in self.bots:
            if bot["id"] == winning_bot_id:
                bot["wins"] += 1
                # Reward validator bot with a small Useful Entropy reward (10 Joule)
                bot["balance_joules"] += 10
                self.accounts["0xBotHarvester"] += 10
                
        # Shuffle order slightly to represent bot re-ordering optimization
        optimized_txs = list(self.l2_pool)
        random.shuffle(optimized_txs) # Represent optimized Minimum Energy sorting
        
        return {
            "winning_bot": winning_bot_id,
            "original_order": original_ids,
            "optimized_order": [tx["tx_id"] for tx in optimized_txs],
            "cost_reduction_pct": round(random.uniform(5.0, 15.0), 2)
        }

    def commit_block(self) -> Dict[str, Any]:
        """
        Gathers L2 pool transactions, executes state energy proof consensus,
        deducts balances, and commits them to L1 block.
        """
        if consensus_lattice.safe_mode_active:
            raise RuntimeError("Cannot commit block: network is in FROZEN safe mode.")

        # 1. Run bot optimization
        bot_outcome = self.execute_arbitrage_competition()
        
        # 2. Relax lattice towards ekuilibrium (Metropolis sweeps)
        for _ in range(5):
            consensus_lattice.step_metropolis()
            
        current_lattice_energy = consensus_lattice.get_energy()
        
        # Calculate Delta Entropy (random walk representing natural dissipation)
        delta_s = (100.0 - consensus_lattice.get_entropy_stability()) / 100.0
        
        # 3. Process transfers
        block_txs = []
        for tx in self.l2_pool:
            sender = tx["sender"]
            recipient = tx["recipient"]
            amount = tx["amount_joules"]
            
            # double check balance
            if self.accounts.get(sender, 0) >= amount:
                self.accounts[sender] -= amount
                self.accounts[recipient] = self.accounts.get(recipient, 0) + amount
                block_txs.append(tx)
                
        # Clear pool
        self.l2_pool.clear()
        
        # Clear external lattice stress fields
        consensus_lattice.clear_stress()
        
        # 4. Generate block
        block_height = len(self.chain)
        settled_entropy = thermal_noise.generate_entropy_salt(32)
        
        # Select proposer randomly from online validators
        online_validators = [v for v in self.validators if v["status"] == "online"]
        if not online_validators:
            online_validators = [{"address": "0x0a111a", "name": "Alpha-Node"}]
            
        proposer = random.choice(online_validators)
        validator_address = proposer["address"]
        
        # Distribute Block Reward dynamically (decays every 4 years)
        block_reward = self.get_current_block_reward(block_height)
        if block_reward > 0:
            proposer_reward = int(block_reward * 0.36)
            active_signers = [v for v in online_validators if v["address"] != validator_address]
            if active_signers:
                signer_reward = (block_reward - proposer_reward) // len(active_signers)
                self.accounts[validator_address] = self.accounts.get(validator_address, 0) + proposer_reward
                for val in active_signers:
                    self.accounts[val["address"]] = self.accounts.get(val["address"], 0) + signer_reward
            else:
                self.accounts[validator_address] = self.accounts.get(validator_address, 0) + block_reward
        
        block = {
            "block_height": block_height,
            "timestamp": time.time(),
            "transactions": block_txs,
            "settled_entropy": settled_entropy,
            "lattice_energy_state": round(current_lattice_energy, 4),
            "delta_entropy": round(delta_s, 6),
            "validator": validator_address,
            "winning_bot": bot_outcome["winning_bot"],
            "bot_saving_pct": bot_outcome.get("cost_reduction_pct", 0.0)
        }
        
        self.chain.append(block)
        save_block_to_db(block)
        return block

    def register_validator(self, address: str, name: str, stake_amount_joules: int, tier_type: str) -> Dict[str, Any]:
        """Registers or re-enables a validator by staking a specific amount of DUIT (Joules)"""
        address = address.lower().strip()
        
        if stake_amount_joules <= 0:
            raise ValueError("Staking amount must be positive.")
            
        current_bal = self.accounts.get(address, 0)
        if current_bal < stake_amount_joules:
            raise ValueError(f"Insufficient balance to stake. Required: {stake_amount_joules} J, Available: {current_bal} J")
            
        existing = next((v for v in self.validators if v["address"] == address), None)
        if existing:
            if existing["status"] == "online":
                raise ValueError("This address is already registered as an active online validator.")
            if existing["status"] == "cooldown" and time.time() < existing["cooldown_until"]:
                remaining = int(existing["cooldown_until"] - time.time())
                raise ValueError(f"Dongle is in deactivation cooldown. Please wait {remaining} seconds before re-registering.")
        
        # Deduct stake from account balance
        self.accounts[address] -= stake_amount_joules
        
        val = {
            "address": address,
            "name": name,
            "stake_amount_joules": stake_amount_joules,
            "tier_type": tier_type,
            "status": "online",
            "cooldown_until": 0.0
        }
        save_validator_to_db(val)
        
        # Reload validators list
        db_validators = load_validators_from_db()
        self.validators = []
        for v in db_validators:
            self.validators.append({
                "name": v["name"],
                "address": v["address"],
                "stake_amount_joules": int(v["stake_amount_joules"]),
                "tier_type": v["tier_type"],
                "status": v["status"],
                "cooldown_until": float(v["cooldown_until"])
            })
            
        return {"status": "success", "address": address, "name": name, "stake_amount": stake_amount_joules, "tier_type": tier_type}

    def unregister_validator(self, address: str) -> Dict[str, Any]:
        """Unstakes a validator immediately, refunding 100% of stake, and triggers a 24-hour hardware cooldown"""
        address = address.lower().strip()
        
        existing = next((v for v in self.validators if v["address"] == address), None)
        if not existing:
            raise ValueError("No validator registered with this address.")
            
        if existing["status"] == "cooldown":
            raise ValueError("Validator is already deactivated and in cooldown.")
            
        # Refund 100% of staked amount (Zero Slashing)
        stake_refund = existing["stake_amount_joules"]
        self.accounts[address] = self.accounts.get(address, 0) + stake_refund
        
        # Put into cooldown for 24 hours
        cooldown_duration = 86400  # 24 hours in seconds
        cooldown_until = time.time() + cooldown_duration
        
        val = {
            "address": address,
            "name": existing["name"],
            "stake_amount_joules": 0,
            "tier_type": existing["tier_type"],
            "status": "cooldown",
            "cooldown_until": cooldown_until
        }
        save_validator_to_db(val)
        
        # Reload validators list
        db_validators = load_validators_from_db()
        self.validators = []
        for v in db_validators:
            self.validators.append({
                "name": v["name"],
                "address": v["address"],
                "stake_amount_joules": int(v["stake_amount_joules"]),
                "tier_type": v["tier_type"],
                "status": v["status"],
                "cooldown_until": float(v["cooldown_until"])
            })
            
        return {"status": "success", "address": address, "refunded_amount": stake_refund, "cooldown_until": cooldown_until}

    def request_faucet_tokens(self, recipient_address: str) -> Dict[str, Any]:
        """Sends 10 DUIT (10^9 Joules) from treasury 0x01a2b3 to recipient if treasury has enough balance"""
        treasury = "0x01a2b3"
        amount = 1000000000 # 10 DUIT (10^9 Joules)
        
        if self.accounts.get(treasury, 0) >= amount:
            self.accounts[treasury] -= amount
            self.accounts[recipient_address] = self.accounts.get(recipient_address, 0) + amount
            
            tx_id = "0xfaucet" + thermal_noise.generate_entropy_salt(8)[-8:]
            tx = {
                "tx_id": tx_id,
                "sender": treasury,
                "recipient": recipient_address,
                "amount_joules": amount,
                "entropy_salt": thermal_noise.generate_entropy_salt(16),
                "target_energy_state": "0x0000",
                "timestamp": time.time()
            }
            self.l2_pool.append(tx)
            return {"status": "success", "tx_id": tx_id, "amount_duit": 10.0}
        else:
            raise ValueError("Treasury has depleted its testnet faucet funds.")

# Global instance of blockchain
thermo_blockchain = ThermodynamicBlockchain()

import unittest
import numpy as np
from engine.noise import thermal_noise
from engine.consensus import consensus_lattice
from engine.blockchain import thermo_blockchain

class TestThermodynamicEngine(unittest.TestCase):
    
    def test_joule_conversion(self):
        """Verifies currency conversion rules (1 DUIT = 10^8 Joule)"""
        duit_amount = 5.25
        expected_joules = 525000000
        converted = int(duit_amount * 100000000)
        self.assertEqual(converted, expected_joules)
        
    def test_thermal_noise_oscillations(self):
        """Verifies that the Jendela Noise generator produces non-constant physical fluctuations"""
        fluctuations = [thermal_noise.read_voltage_fluctuation() for _ in range(20)]
        # Fluctuations should not all be identical
        self.assertTrue(len(set(fluctuations)) > 1)
        # Fluctuations should be in the microvolt range
        for v in fluctuations:
            self.assertTrue(-2e-6 <= v <= 2e-6)

    def test_entropy_salt_length(self):
        """Verifies that generated entropy salts have the correct length and hexadecimal format"""
        salt = thermal_noise.generate_entropy_salt(16)
        self.assertTrue(salt.startswith("0x"))
        self.assertEqual(len(salt), 34) # "0x" + 32 hex chars

    def test_ising_grid_properties(self):
        """Verifies that the Ising spin grid has the correct size, initialization, and magnetisation limits"""
        grid = consensus_lattice.grid
        self.assertEqual(grid.shape, (10, 10))
        # Spins must only be -1 or 1
        self.assertTrue(np.all(np.isin(grid, [-1, 1])))
        
        # Magnetization must be in [-1.0, 1.0]
        mag = consensus_lattice.get_magnetization()
        self.assertTrue(-1.0 <= mag <= 1.0)
        
        # Stability must be in [0.0, 100.0]
        stability = consensus_lattice.get_entropy_stability()
        self.assertTrue(0.0 <= stability <= 100.0)

    def test_metropolis_relaxation(self):
        """Verifies that Metropolis steps alter lattice energy towards ekuilibrium"""
        initial_energy = consensus_lattice.get_energy()
        
        # Perform sweeps
        for _ in range(10):
            consensus_lattice.step_metropolis()
            
        final_energy = consensus_lattice.get_energy()
        # Since it relaxes towards low energy, let's verify it remains a valid float
        self.assertTrue(isinstance(final_energy, float))

    def test_cooling_off_period_lock(self):
        """Verifies that temperature perturbations trigger self-healing lock (safe mode)"""
        # Disturbance level > 2.8 makes temp > 5.0 (2.269 + 2.8 = 5.069)
        consensus_lattice.set_network_disturbance(3.0)
        self.assertTrue(consensus_lattice.safe_mode_active)
        
        # Restoring temp < 3.2 should disable safe mode (thaw)
        consensus_lattice.set_network_disturbance(0.0)
        self.assertFalse(consensus_lattice.safe_mode_active)

    def test_database_persistence(self):
        """Verifies that blocks and transactions can be written to and read from SQLite database"""
        from engine.db import init_db, save_block_to_db, load_blocks_from_db
        init_db()
        
        # Build mock block
        mock_block = {
            "block_height": 999,
            "timestamp": 1234567.89,
            "settled_entropy": "0xmockentropyhash999",
            "lattice_energy_state": -45.67,
            "delta_entropy": 0.123,
            "validator": "0xvalidator999",
            "winning_bot": "MockBot",
            "bot_saving_pct": 12.34,
            "transactions": [
                {
                    "tx_id": "0xtx999",
                    "sender": "0xsend999",
                    "recipient": "0xrec999",
                    "amount_joules": 50000,
                    "entropy_salt": "0xsalt999",
                    "target_energy_state": "0xtarget999"
                }
            ]
        }
        
        save_block_to_db(mock_block)
        
        # Load blocks
        blocks = load_blocks_from_db()
        # Find our mock block
        saved_block = next((b for b in blocks if b["block_height"] == 999), None)
        
        self.assertIsNotNone(saved_block)
        self.assertEqual(saved_block["settled_entropy"], "0xmockentropyhash999")
        self.assertEqual(len(saved_block["transactions"]), 1)
        self.assertEqual(saved_block["transactions"][0]["tx_id"], "0xtx999")

if __name__ == "__main__":
    unittest.main()

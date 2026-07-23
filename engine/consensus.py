import numpy as np
import math
import random
from engine.noise import thermal_noise

class IsingLatticeConsensus:
    """
    Simulates State Energy Proof (SEP) consensus using a 2D Ising Lattice model.
    The lattice spins (-1 and +1) represent validator node states.
    Validation requires the network to settle into a Minimum Energy Path (MEP)
    equilibrium governed by physical entropy laws.
    """
    def __init__(self, size: int = 10, initial_temp: float = 2.269):
        # 2.269 is the critical temperature (Onsager's critical temperature for 2D Ising)
        self.size = size
        self.temperature = initial_temp # System temperature (controls thermal noise)
        self.coupling_constant = 1.0 # J coupling constant
        self.grid = np.random.choice([-1, 1], size=(size, size))
        self.magnetic_field = np.zeros((size, size)) # External transaction influence
        self.safe_mode_active = False # True = Network frozen (Cooling-Off)

    def get_energy(self) -> float:
        """Calculates total Hamiltonian energy of the lattice: E = -J sum(s_i * s_j) - sum(H_i * s_i)"""
        energy = 0.0
        for r in range(self.size):
            for c in range(self.size):
                s = self.grid[r, c]
                # Nearest neighbors with periodic boundary conditions
                neighbors = (
                    self.grid[(r + 1) % self.size, c] +
                    self.grid[(r - 1) % self.size, c] +
                    self.grid[r, (c + 1) % self.size] +
                    self.grid[r, (c - 1) % self.size]
                )
                energy += -self.coupling_constant * s * neighbors
                # Add external magnetic field (transaction influences)
                energy += -self.magnetic_field[r, c] * s
        # Divide by 2 because each pair is counted twice
        return energy / 2.0

    def get_magnetization(self) -> float:
        """Calculates the net magnetization (net spin alignment) of the network: M = sum(s_i) / N"""
        return float(np.mean(self.grid))

    def get_entropy_stability(self) -> float:
        """
        Calculates network stability based on system entropy.
        Perfect order (spins all +1 or all -1) -> 100% stability.
        Perfect disorder (maximum entropy) -> 0% stability.
        """
        mag = abs(self.get_magnetization())
        # Model entropy: S = -p ln(p) - (1-p) ln(1-p) where p is probability of spin +1
        p = (mag + 1.0) / 2.0
        if p <= 0.0 or p >= 1.0:
            entropy = 0.0
        else:
            entropy = - (p * math.log(p) + (1.0 - p) * math.log(1.0 - p))
        
        # Max entropy is ln(2) = 0.69315
        max_entropy = math.log(2.0)
        normalized_entropy = entropy / max_entropy
        stability = (1.0 - normalized_entropy) * 100.0
        return max(0.0, min(100.0, stability))

    def step_metropolis(self):
        """
        Performs one full sweep of Metropolis Monte Carlo relaxation.
        Allows the sirkuit to relax towards minimum energy.
        """
        if self.safe_mode_active:
            # Under Cooling-off freeze, temperatures collapse to absolute zero
            temp = 0.01
        else:
            temp = self.temperature

        for _ in range(self.size * self.size):
            r = random.randint(0, self.size - 1)
            c = random.randint(0, self.size - 1)
            s = self.grid[r, c]
            
            # Sum of neighbors
            neighbors = (
                self.grid[(r + 1) % self.size, c] +
                self.grid[(r - 1) % self.size, c] +
                self.grid[r, (c + 1) % self.size] +
                self.grid[r, (c - 1) % self.size]
            )
            
            # Change in energy if we flip this spin
            dE = 2 * self.coupling_constant * s * neighbors + 2 * self.magnetic_field[r, c] * s
            
            # Acceptance probability
            if dE <= 0:
                self.grid[r, c] = -s
            elif temp > 0.0 and random.random() < math.exp(-dE / temp):
                self.grid[r, c] = -s

    def apply_transaction_stress(self, sender_key: str, recipient_key: str, amount_joules: int):
        """
        Maps a transaction's value and address signature to localized physical fields.
        This forces the lattice to adapt, acting as a computation workload.
        """
        # Determine coordinates based on public keys
        s_hash = hash(sender_key)
        r_hash = hash(recipient_key)
        
        # Coordinates in 10x10 lattice
        r1, c1 = (s_hash % self.size), ((s_hash // self.size) % self.size)
        r2, c2 = (r_hash % self.size), ((r_hash // self.size) % self.size)
        
        # Stress scale depends on amount in Joules
        stress_field = (amount_joules / 1e8) * 0.5 # capped scaling
        
        # Impose local external magnetic field
        self.magnetic_field[r1, c1] += stress_field
        self.magnetic_field[r2, c2] -= stress_field

    def clear_stress(self):
        """Restores network parameters back to equilibrium baseline"""
        self.magnetic_field = np.zeros((self.size, self.size))

    def evaluate_state_energy_proof(self, target_energy: float) -> bool:
        """
        Checks if the local transaction state achieves thermodynamic equilibrium.
        Verification succeeds if the current lattice energy matches the target energy
        within a tolerance bounds, indicating that the Minimum Energy Path was followed.
        """
        if self.safe_mode_active:
            return False
            
        current_energy = self.get_energy()
        # Tolerance margin corresponds to simulated thermal noise fluctuations
        tolerance = abs(thermal_noise.read_voltage_fluctuation() * 1e8) + 10.0
        
        is_valid = abs(current_energy - target_energy) <= tolerance
        return is_valid

    def set_network_disturbance(self, disturbance_level: float):
        """
        Simulates external disruptions (temperature spikes, power draw, network splits).
        If temperature spikes too far, system enters natural Cooling-Off Lock.
        """
        # Normal range is ~1.5 to 3.0. Disturbance adds directly to Temperature
        self.temperature = 2.269 + disturbance_level
        
        # Check if we trigger Cooling-Off freeze
        if self.temperature > 5.0:
            self.safe_mode_active = True
        elif self.temperature < 3.2 and self.safe_mode_active:
            # Self-healing Thaw when temperature drops back and settles
            self.safe_mode_active = False

# Global instance of consensus engine
consensus_lattice = IsingLatticeConsensus()

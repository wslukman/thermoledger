import time
import os
import math

class ThermalNoiseGenerator:
    """
    Simulates high-frequency hardware thermal noise (Jendela Noise)
    using a combination of system entropy, microsecond timestamps,
    and a chaotic mathematical system (Logistic Map) to emulate atomic flucuations.
    """
    def __init__(self, r: float = 3.999, x_init: float = 0.5):
        # r is the chaotic parameter for the logistic map (r in [3.57, 4.0] is chaotic)
        self.r = r
        self.x = x_init
        self.last_update = time.perf_counter()

    def _step_chaotic_map(self):
        """Steps the chaotic logistic map to update internal state"""
        self.x = self.r * self.x * (1.0 - self.x)
        # Avoid convergence to boundary values
        if self.x < 0.0001 or self.x > 0.9999:
            self.x = 0.51234
        return self.x

    def read_voltage_fluctuation(self) -> float:
        """
        Simulates physical micro-voltage fluctuations of a thermal noise circuit.
        Returns a value in Volts (e.g., in the microvolt range around 0V).
        """
        # Step chaotic map
        c_val = self._step_chaotic_map()
        
        # Combine with system high-res timer
        t = time.perf_counter_ns()
        t_osc = math.sin(t / 1000.0) # sub-microsecond oscillation
        
        # Pull 1 byte of OS system entropy to add hardware-level randomness
        sys_byte = ord(os.urandom(1)) / 255.0
        
        # Combine parameters to simulate thermal noise voltage fluctuation (microvolts)
        # Thermal noise v_t = sqrt(4 * k_B * T * R * delta_f)
        # We model this as a wave fluctuating between -1.0uV and +1.0uV
        fluctuation = (c_val * 0.4 + t_osc * 0.3 + sys_byte * 0.3) * 2.0 - 1.0
        return fluctuation * 1e-6 # in Volts

    def generate_entropy_salt(self, length: int = 32) -> str:
        """
        Generates a cryptographic key/salt (One-Time Pad representation)
        derived directly from simulated physical thermal noise.
        """
        entropy_bytes = bytearray()
        for _ in range(length):
            # Sample multiple voltage fluctuations and hash them to form bytes
            samples = []
            for _ in range(8):
                # Micro-delay to let time step advance
                v = self.read_voltage_fluctuation()
                samples.append(v)
            
            # Map samples to a single byte
            val = int(sum(abs(s) * 1e7 for s in samples) * 256) % 256
            # Mix with actual OS entropy to guarantee cryptographic strength
            sys_rand = os.urandom(1)[0]
            entropy_bytes.append(val ^ sys_rand)
            
        return "0x" + entropy_bytes.hex()

# Global instance of noise generator
thermal_noise = ThermalNoiseGenerator()

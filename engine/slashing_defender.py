import json
import os
import threading

class SlashingDefenderException(Exception):
    """Exception raised when a signing request violates the double-signing safety rules."""
    pass

class SlashingDefender:
    def __init__(self, state_file_path: str = "priv_validator_state.json"):
        self.state_file_path = state_file_path
        self.lock = threading.Lock()
        self._ensure_state_file()

    def _ensure_state_file(self):
        """Ensures that the state tracking file exists with a default initial state."""
        if not os.path.exists(self.state_file_path):
            self._save_state(0, 0, "")

    def _load_state(self):
        """Loads the current signing state from the JSON file."""
        try:
            with open(self.state_file_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"last_height": 0, "last_round": 0, "last_block_hash": ""}

    def _save_state(self, height: int, round_num: int, block_hash: str):
        """Saves the new signing state to the JSON file."""
        state = {
            "last_height": height,
            "last_round": round_num,
            "last_block_hash": block_hash
        }
        with open(self.state_file_path, "w") as f:
            json.dump(state, f, indent=4)

    def check_and_record_signing(self, height: int, round_num: int, block_hash: str):
        """
        Verifies if signing the block hash at the specified height and round is safe.
        If safe, it updates the state file and returns True.
        If unsafe, it raises a SlashingDefenderException.
        """
        with self.lock:
            state = self._load_state()
            last_height = state.get("last_height", 0)
            last_block_hash = state.get("last_block_hash", "")
            
            # Rule 1: Cannot sign for a past height
            if height < last_height:
                raise SlashingDefenderException(
                    f"Double-signing prevention: Requested height {height} is lower than last signed height {last_height}."
                )
                
            # Rule 2: At the same height, can only sign the exact same block hash
            if height == last_height:
                if block_hash != last_block_hash and last_block_hash != "":
                    raise SlashingDefenderException(
                        f"Double-signing attempt detected! Attempted to sign a different block hash '{block_hash}' at height {height}. Last signed hash was '{last_block_hash}'."
                    )
                # If it's the same hash, it is a safe re-signing (no update needed)
                return True
                
            # Rule 3: For new heights, always safe to sign
            self._save_state(height, round_num, block_hash)
            return True

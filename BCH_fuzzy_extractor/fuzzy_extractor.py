from .bch_codec import BCHCodec
from .utils import generate_random_bytes, xor_bytes
from .storage import Storage

class FuzzyExtractor:
    def __init__(self, db_path='helper_data.db'):
        # t=64, m=13 (8191-bit field)
        self.codec = BCHCodec(t=64, m=13)
        self.storage = Storage(db_path)

    def generate(self, user_id, biometric_input):
        """
        Enrollment step:
        Receive biometric input (3488 bits), generate helper and extract a secret key.
        """
        if len(biometric_input) != 436: # 3488 bits / 8 = 436 bytes
            raise ValueError(f"Input vector length must be 436 bytes. (current: {len(biometric_input)})")

        # 1. Generate random secret message
        # (size = codec.data_bytes)
        secret_msg = generate_random_bytes(self.codec.data_bytes)

        # 2. Create codeword by encoding the secret
        codeword = self.codec.encode(secret_msg)

        # 3. Create helper data: helper = biometric XOR codeword
        helper = xor_bytes(biometric_input, codeword)

        # 4. Save helper
        self.storage.save_helper(user_id, helper)

        # 5. Return the secret
        return secret_msg

    def reproduce(self, user_id, biometric_noisy):
        """
        Authentication step:
        Use the noisy biometric and stored helper to recover the original secret.
        """
        if len(biometric_noisy) != 436:
            raise ValueError("Input vector length mismatch.")

        # 1. Load helper
        helper = self.storage.load_helper(user_id)
        if helper is None:
            raise ValueError("User not enrolled.")

        # 2. Reconstruct the noisy codeword: R' = helper XOR biometric_noisy
        # (since helper = R XOR Bio, helper XOR Bio_noisy = R XOR (Bio XOR Bio_noisy) = R XOR Error)
        codeword_noisy = xor_bytes(helper, biometric_noisy)

        # 3. Decode (error correction)
        try:
            # If there are <= t bit errors, the original secret message is returned
            recovered_secret = self.codec.decode(codeword_noisy)
            return recovered_secret
        except RuntimeError:
            # Recovery failed (errors exceed correctable threshold)
            return None
# test_simulation.py

import random
from BCH_fuzzy_extractor.fuzzy_extractor import FuzzyExtractor


# ==========================================
# Helper functions: string <-> bytes conversion
# ==========================================
def string_to_bytes(binary_str):
    """Convert '010101...' string into bytes object."""
    # 3488 bits = 436 bytes
    return int(binary_str, 2).to_bytes(436, byteorder='big')


def bytes_to_string(data_bytes):
    """Convert bytes object into '010101...' string."""
    # Pad with leading zeros to length 3488
    return format(int.from_bytes(data_bytes, byteorder='big'), '03488b')


def inject_noise_to_string(binary_str, error_count):
    """Inject noise by flipping bits in the binary string."""
    str_list = list(binary_str)
    indices = random.sample(range(len(str_list)), error_count)

    print(f"   -> [Noise] Flipping {error_count} bits.")
    for idx in indices:
        # Flip 0->1 or 1->0
        str_list[idx] = '1' if str_list[idx] == '0' else '0'

    return "".join(str_list)


# ==========================================
# Scenario test
# ==========================================

def run_scenario():
    print("=== [Team project scenario] CNN output (string) integration test ===")

    fe = FuzzyExtractor()
    user_id = "user_20201234"

    # 1. Assume CNN outputs a 3488-bit binary string
    cnn_output_str = "".join(random.choice('01') for _ in range(3488))
    print(f"1. CNN output (Original) length: {len(cnn_output_str)} bits")

    # 2. Preprocess: string -> bytes for Fuzzy Extractor input
    original_bytes = string_to_bytes(cnn_output_str)

    # 3. Enrollment: Generate helper and secret key
    secret_key = fe.generate(user_id, original_bytes)
    print(f"2. Secret key generated: {secret_key.hex()[:16]}...")
    print("   (Helper data saved to DB.)")

    print("-" * 50)

    # 4. Later, login attempt with noise
    noise_amount = 60  # should succeed up to 64 errors
    noisy_cnn_output_str = inject_noise_to_string(cnn_output_str, noise_amount)

    # convert back to bytes
    noisy_bytes = string_to_bytes(noisy_cnn_output_str)

    # 5. Authentication: Reproduce
    print("3. Attempting authentication (reproduce)...")
    recovered_key = fe.reproduce(user_id, noisy_bytes)

    # 6. Result
    if recovered_key:
        print(f"4. Recovered key: {recovered_key.hex()[:16]}...")
        if recovered_key == secret_key:
            print("\n>>> [SUCCESS] Fully recovered! (authentication success)")
        else:
            print("\n>>> [FAIL] Key recovered but does not match original. (logical error)")
    else:
        print("\n>>> [FAIL] Recovery failed (errors exceeded 64 bits or DB error)")


if __name__ == "__main__":
    run_scenario()
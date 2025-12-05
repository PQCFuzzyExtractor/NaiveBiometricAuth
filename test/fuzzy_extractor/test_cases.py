import random
import os
from BCH_fuzzy_extractor.fuzzy_extractor import FuzzyExtractor


# ==========================================
# Test utility functions
# ==========================================
def inject_bit_errors(data_bytes, num_errors):
    """Flip exactly num_errors bits in the input byte data."""
    data_array = bytearray(data_bytes)
    total_bits = len(data_bytes) * 8

    # Select unique random bit positions
    error_indices = random.sample(range(total_bits), num_errors)

    for idx in error_indices:
        byte_pos = idx // 8
        bit_pos = idx % 8  # 0~7
        # Flip the bit (XOR 1)
        mask = 1 << (7 - bit_pos)  # Big Endian bit ordering
        data_array[byte_pos] ^= mask

    return bytes(data_array)


def run_single_case(case_name, fe, input_data, error_count, expect_success):
    """Run a single test case."""
    print(f"\n[Case: {case_name}]")
    print(f" - Input data length: {len(input_data)} bytes")
    print(f" - Number of injected bit errors: {error_count} bits")

    user_id = f"user_{case_name}"

    # 1. Enrollment (Generate)
    try:
        original_key = fe.generate(user_id, input_data)
    except Exception as e:
        print(f"FAIL: Error during enrollment - {e}")
        return False

    # 2. Inject errors
    noisy_input = inject_bit_errors(input_data, error_count)

    # 3. Reproduce
    try:
        recovered_key = fe.reproduce(user_id, noisy_input)
    except Exception as e:
        print(f"LOG: Exception during reproduce logic ({e})")
        recovered_key = None

    # 4. Verify
    if expect_success:
        if recovered_key == original_key:
            print("PASS: Key recovery succeeded (expected)")
            return True
        else:
            print("FAIL: Key recovery failed (expected success)")
            return False
    else:
        if recovered_key is None:
            print("PASS: Recovery failed as expected")
            return True
        elif recovered_key != original_key:
            print("PASS: Recovered a different key (treated as failure)")
            return True
        else:
            print("FAIL: Unexpected successful recovery (serious issue)")
            return False


# ==========================================
# Main test runner
# ==========================================
def run_all_tests():
    print("=" * 60)
    print("     Fuzzy Extractor Comprehensive Stress Test (Robustness)")
    print("=" * 60)

    # Initialize (DB/table creation may take time)
    fe = FuzzyExtractor()

    # Dummy data generator: 436 bytes == 3488 bits
    def get_random_bio():
        return os.urandom(436)

    # ---------------------------------------------------------
    # Case 1: Basic functionality (0 errors)
    # ---------------------------------------------------------
    run_single_case(
        "Basic_No_Error",
        fe,
        get_random_bio(),
        error_count=0,
        expect_success=True
    )

    # ---------------------------------------------------------
    # Case 2: Boundary test (exactly 64 bit errors - should succeed)
    # ---------------------------------------------------------
    run_single_case(
        "Boundary_Max_64",
        fe,
        get_random_bio(),
        error_count=64,
        expect_success=True
    )

    # ---------------------------------------------------------
    # Case 3: Over-limit test (65 bit errors - should fail)
    # ---------------------------------------------------------
    run_single_case(
        "Over_Limit_65",
        fe,
        get_random_bio(),
        error_count=65,
        expect_success=False
    )

    # ---------------------------------------------------------
    # Case 4: Edge case - All Zeros
    # ---------------------------------------------------------
    all_zeros = bytes([0] * 436)
    run_single_case(
        "Pattern_All_Zeros",
        fe,
        all_zeros,
        error_count=30,
        expect_success=True
    )

    # ---------------------------------------------------------
    # Case 5: Edge case - All Ones
    # ---------------------------------------------------------
    all_ones = bytes([0xFF] * 436)
    run_single_case(
        "Pattern_All_Ones",
        fe,
        all_ones,
        error_count=30,
        expect_success=True
    )

    # ---------------------------------------------------------
    # Case 6: Stability test (Random 100 runs)
    # ---------------------------------------------------------
    print("\n[Case: Stability_Random_100]")
    success_count = 0
    total_runs = 100
    print(f" - Running {total_runs} random iterations...", end="", flush=True)

    for i in range(total_runs):
        # Random number of errors between 0 and 64
        rand_err = random.randint(0, 64)
        bio = get_random_bio()

        uid = f"stab_{i}"
        k_org = fe.generate(uid, bio)
        bio_noisy = inject_bit_errors(bio, rand_err)
        k_rec = fe.reproduce(uid, bio_noisy)

        if k_org == k_rec:
            success_count += 1

        if i % 10 == 0:
            print(".", end="", flush=True)

    print(f"\n - Result: {success_count}/{total_runs} successes")
    if success_count == total_runs:
        print("PASS: 100/100 stability test passed")
    else:
        print("FAIL: Some runs failed during stability test")


if __name__ == "__main__":
    run_all_tests()
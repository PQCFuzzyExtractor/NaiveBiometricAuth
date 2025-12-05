from feature_extraction_module.extract_feature_arcface import extract_iris_code, init_model, compare_iris
from BCH_fuzzy_extractor.fuzzy_extractor import FuzzyExtractor
import os

from feature_extraction_module.utils import iris_code_to_bytes, set_seed
import numpy as np

same_image_one = "source/same1.jpg"
same_image_two = "source/same2.jpg"
different_image = "source/diff.jpg"

DB_PATH = "helper_test.db"
USER_ID = "user_test_case"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def debug_repeatability(image_path, repeats=2):
    codes = [extract_iris_code(image_path) for _ in range(repeats)]
    # pairwise hamming distances vs first
    dists = [int(np.sum(codes[0] != c)) for c in codes[1:]]
    print(f"[DEBUG] '{image_path}' repeatability ({repeats}) Hamming distances (vs first): {dists}")
    return codes[0]


def run_case():
    # 0) Fix seed and initialize model
    set_seed(42)
    init_model(seed=42)

    fe = FuzzyExtractor(db_path=DB_PATH)

    # 1) Generate helper using same_image_one
    print("[STEP] Enrollment (Generate) using same_image_one")
    code_enroll = debug_repeatability(same_image_one, repeats=2)
    bio_enroll = iris_code_to_bytes(code_enroll)
    secret_key = fe.generate(USER_ID, bio_enroll)
    print(f" - Generated secret key length: {len(secret_key)} bytes")

    # 2) Authenticate with same_image_two
    print("\n[STEP] Authentication with same_image_two (expected: SUCCESS)")
    # repeatability for same_image_two
    code_same = debug_repeatability(same_image_two, repeats=2)
    code_same[0] ^= 1
    bio_same = iris_code_to_bytes(code_same)

    # hamming enroll vs same
    hd_enroll_same = int(np.sum(code_enroll != code_same))
    print(f"[INFO] enroll vs same Hamming: {hd_enroll_same}")

    recovered_same = fe.reproduce(USER_ID, bio_same)
    if recovered_same is None:
        print(" - RESULT: Recovery failed (unexpected for same person)")
    elif recovered_same == secret_key:
        print(" - RESULT: Recovery succeeded, keys match (expected)")
    else:
        print(" - RESULT: Recovered but key mismatch (abnormal)")

    # 3) Authenticate with different_image
    print("\n[STEP] Authentication with different_image (expected: FAIL or different key)")
    code_diff = debug_repeatability(different_image, repeats=2)
    bio_diff = iris_code_to_bytes(code_diff)
    hd_enroll_diff = int(np.sum(code_enroll != code_diff))
    print(f"[INFO] enroll vs diff Hamming: {hd_enroll_diff}")

    recovered_diff = fe.reproduce(USER_ID, bio_diff)
    if recovered_diff is None:
        print(" - RESULT: Recovery failed (as expected for different person)")
    elif recovered_diff == secret_key:
        print(" - RESULT: Recovery succeeded and keys match (unexpected: different person matched)")
    else:
        print(" - RESULT: Recovered but key mismatch (different key)")


if __name__ == "__main__":
    run_case()

import numpy as np
import random
import os
from fuzzy_extractor.fuzzy_extractor import FuzzyExtractor
from fuzzy_extractor.utils import xor_bytes


# ==========================================
# 테스트 유틸리티 함수
# ==========================================
def inject_bit_errors(data_bytes, num_errors):
    """바이트 데이터에 정확히 num_errors 개수만큼 비트 반전을 일으킴"""
    data_array = bytearray(data_bytes)
    total_bits = len(data_bytes) * 8

    # 중복되지 않는 랜덤 비트 위치 선택
    error_indices = random.sample(range(total_bits), num_errors)

    for idx in error_indices:
        byte_pos = idx // 8
        bit_pos = idx % 8  # 0~7
        # 해당 비트 반전 (XOR 1)
        mask = 1 << (7 - bit_pos)  # Big Endian 기준
        data_array[byte_pos] ^= mask

    return bytes(data_array)


def run_single_case(case_name, fe, input_data, error_count, expect_success):
    """단일 테스트 케이스 실행 함수"""
    print(f"\n[Case: {case_name}]")
    print(f" - 입력 데이터 크기: {len(input_data)} bytes")
    print(f" - 주입할 에러 수: {error_count} bits")

    user_id = f"user_{case_name}"

    # 1. 등록 (Generate)
    try:
        original_key = fe.generate(user_id, input_data)
    except Exception as e:
        print(f"FAIL: 등록 중 에러 발생 - {e}")
        return False

    # 2. 에러 주입
    noisy_input = inject_bit_errors(input_data, error_count)

    # 3. 복구 (Reproduce)
    try:
        recovered_key = fe.reproduce(user_id, noisy_input)
    except Exception as e:
        print(f"LOG: 복구 로직 실행 중 예외 발생 ({e})")
        recovered_key = None

    # 4. 검증
    if expect_success:
        if recovered_key == original_key:
            print("PASS: 키 복구 성공 (예상대로 성공함)")
            return True
        else:
            print("FAIL: 키 복구 실패 (성공했어야 함)")
            return False
    else:
        if recovered_key is None:
            print("PASS: 복구 실패 처리됨 (예상대로 실패함)")
            return True
        elif recovered_key != original_key:
            print("PASS: 엉뚱한 키가 나왔으나 원본과 다름 (실패로 간주)")
            return True
        else:
            print("FAIL: 복구되면 안 되는데 복구됨 (심각한 오류)")
            return False


# ==========================================
# 메인 테스트 실행
# ==========================================
def run_all_tests():
    print("=" * 60)
    print("     Fuzzy Extractor 종합 부하 테스트 (Robustness Test)")
    print("=" * 60)

    # 초기화 (테이블 생성 시간 소요 가능)
    fe = FuzzyExtractor()

    # 436바이트 (3488비트) 더미 데이터 생성기
    def get_random_bio():
        return os.urandom(436)

    # ---------------------------------------------------------
    # Case 1: 기본 기능 테스트 (에러 0개)
    # ---------------------------------------------------------
    run_single_case(
        "Basic_No_Error",
        fe,
        get_random_bio(),
        error_count=0,
        expect_success=True
    )

    # ---------------------------------------------------------
    # Case 2: 경계값 테스트 (정확히 64비트 에러 - 성공해야 함)
    # ---------------------------------------------------------
    # 이론상 최대치인 64비트가 깨져도 복구되는지 확인
    run_single_case(
        "Boundary_Max_64",
        fe,
        get_random_bio(),
        error_count=64,
        expect_success=True
    )

    # ---------------------------------------------------------
    # Case 3: 한계 초과 테스트 (65비트 에러 - 실패해야 함)
    # ---------------------------------------------------------
    # 65비트부터는 수학적으로 복구가 불가능하거나 오동작해야 함
    run_single_case(
        "Over_Limit_65",
        fe,
        get_random_bio(),
        error_count=65,
        expect_success=False
    )

    # ---------------------------------------------------------
    # Case 4: 특이값 테스트 - All Zeros (0000...)
    # ---------------------------------------------------------
    # 패딩 로직이 0을 다루므로, 입력이 전부 0일 때 꼬이지 않는지 확인
    all_zeros = bytes([0] * 436)
    run_single_case(
        "Pattern_All_Zeros",
        fe,
        all_zeros,
        error_count=30,
        expect_success=True
    )

    # ---------------------------------------------------------
    # Case 5: 특이값 테스트 - All Ones (1111...)
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
    # Case 6: 반복 안정성 테스트 (Random 100회)
    # ---------------------------------------------------------
    print("\n[Case: Stability_Random_100]")
    success_count = 0
    total_runs = 100
    print(f" - 랜덤 데이터로 {total_runs}회 반복 테스트 진행 중...", end="", flush=True)

    for i in range(total_runs):
        # 0 ~ 64 사이의 랜덤한 에러 개수 적용
        rand_err = random.randint(0, 64)
        bio = get_random_bio()

        # 직접 함수 호출 대신 로직 수행
        uid = f"stab_{i}"
        k_org = fe.generate(uid, bio)
        bio_noisy = inject_bit_errors(bio, rand_err)
        k_rec = fe.reproduce(uid, bio_noisy)

        if k_org == k_rec:
            success_count += 1

        if i % 10 == 0:
            print(".", end="", flush=True)

    print(f"\n - 결과: {success_count}/{total_runs} 성공")
    if success_count == total_runs:
        print("PASS: 100회 반복 테스트 통과")
    else:
        print("FAIL: 반복 테스트 중 실패 사례 발생")


if __name__ == "__main__":
    run_all_tests()
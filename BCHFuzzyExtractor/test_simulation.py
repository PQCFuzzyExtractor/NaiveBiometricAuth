# test_simulation.py

import random
from BCHFuzzyExtractor.fuzzy_extractor import FuzzyExtractor


# ==========================================
# 도우미 함수: 문자열 <-> 바이트 변환
# ==========================================
def string_to_bytes(binary_str):
    """ '010101...' 문자열을 bytes 객체로 변환 """
    # 3488비트 = 436바이트
    return int(binary_str, 2).to_bytes(436, byteorder='big')


def bytes_to_string(data_bytes):
    """ bytes 객체를 '010101...' 문자열로 변환 """
    # 빈 자리는 0으로 채워서 3488길이 맞춤
    return format(int.from_bytes(data_bytes, byteorder='big'), '03488b')


def inject_noise_to_string(binary_str, error_count):
    """ 문자열 상태에서 비트를 반전시켜 노이즈 주입 """
    str_list = list(binary_str)
    indices = random.sample(range(len(str_list)), error_count)

    print(f"   -> [Noise] {error_count}개의 비트를 반전시킵니다.")
    for idx in indices:
        # 0이면 1로, 1이면 0으로 변경
        str_list[idx] = '1' if str_list[idx] == '0' else '0'

    return "".join(str_list)


# ==========================================
# 시나리오 테스트 시작
# ==========================================
def run_scenario():
    print("=== [팀 프로젝트 시나리오] CNN 출력(문자열) 연동 테스트 ===")

    fe = FuzzyExtractor()
    user_id = "user_20201234"  # 학번 등 식별자

    # 1. [가정] CNN 모델이 3488 길이의 이진 문자열을 출력했다고 가정
    # (실제로는 모델 출력값을 여기서 받으세요)
    cnn_output_str = "".join(random.choice('01') for _ in range(3488))
    print(f"1. CNN 출력(Original) 길이: {len(cnn_output_str)} bits")

    # 2. [전처리] 문자열 -> 바이트 변환 (Fuzzy Extractor 입력용)
    original_bytes = string_to_bytes(cnn_output_str)

    # 3. [등록] Generate 실행
    # 여기서 나온 key는 나중에 McEliece 암호키로 쓰거나 서버에 등록
    secret_key = fe.generate(user_id, original_bytes)
    print(f"2. 키 생성 완료 (Secret): {secret_key.hex()[:16]}...")
    print("   (Helper 데이터가 DB에 저장되었습니다.)")

    print("-" * 50)

    # 4. [상황] 나중에 다시 로그인 시도 (노이즈 발생)
    # 홍채 인식 과정에서 조명, 각도 등으로 값이 약간 달라짐
    noise_amount = 60  # 64개까지는 성공해야 함
    noisy_cnn_output_str = inject_noise_to_string(cnn_output_str, noise_amount)

    # 다시 바이트로 변환
    noisy_bytes = string_to_bytes(noisy_cnn_output_str)

    # 5. [인증] Reproduce 실행
    print("3. 인증 시도 (복구 시작)...")
    recovered_key = fe.reproduce(user_id, noisy_bytes)

    # 6. 결과 확인
    if recovered_key:
        print(f"4. 복구된 키: {recovered_key.hex()[:16]}...")
        if recovered_key == secret_key:
            print("\n>>> [SUCCESS] 완벽하게 복원되었습니다! (인증 성공)")
        else:
            print("\n>>> [FAIL] 키가 복원되었으나 원본과 다릅니다. (심각한 논리 오류)")
    else:
        print("\n>>> [FAIL] 복원 실패 (허용 오차 64비트를 초과했거나 DB 오류)")


if __name__ == "__main__":
    run_scenario()
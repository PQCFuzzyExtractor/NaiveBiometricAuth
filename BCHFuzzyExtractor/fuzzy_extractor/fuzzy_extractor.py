from .bch_codec import BCHCodec
from .utils import generate_random_bytes, xor_bytes
from .storage import Storage

class FuzzyExtractor:
    def __init__(self, db_path='helper_data.db'):
        # t=64, m=13 (8191비트 체계)
        self.codec = BCHCodec(t=64, m=13)
        self.storage = Storage(db_path)

    def generate(self, user_id, biometric_input):
        """
        등록(Enrollment) 단계:
        생체 정보(3488비트)를 입력받아 Helper를 생성하고 키를 추출함.
        """
        if len(biometric_input) != 436: # 3488 bits / 8 = 436 bytes
            raise ValueError(f"입력 벡터 길이는 반드시 436 바이트여야 합니다. (현재: {len(biometric_input)})")

        # 1. 랜덤 키(Secret Message) 생성
        # (BCH 데이터 영역 크기만큼 생성: 436 - ecc_bytes)
        secret_msg = generate_random_bytes(self.codec.data_bytes)

        # 2. 코드워드 생성 (R)
        # R = Encode(Secret) -> 길이는 436바이트가 됨
        codeword = self.codec.encode(secret_msg)

        # 3. Helper 데이터 생성 (P)
        # P = Biometric XOR Codeword
        helper = xor_bytes(biometric_input, codeword)

        # 4. Helper 저장
        self.storage.save_helper(user_id, helper)

        # 5. 키 반환 (생성된 랜덤 시크릿 메시지)
        # 이 값이 추후 McEliece의 시드나 키로 사용됨
        return secret_msg

    def reproduce(self, user_id, biometric_noisy):
        """
        인증(Authentication) 단계:
        노이즈가 섞인 생체 정보와 저장된 Helper를 이용해 원본 키 복원.
        """
        if len(biometric_noisy) != 436:
            raise ValueError("입력 벡터 길이가 다릅니다.")

        # 1. Helper 로드
        helper = self.storage.load_helper(user_id)
        if helper is None:
            raise ValueError("등록되지 않은 사용자입니다.")

        # 2. 노이즈가 섞인 코드워드 복원 (R')
        # R' = Helper XOR Biometric_Noisy
        # (Helper = R XOR Bio) 이므로 (R XOR Bio XOR Bio_Noisy) = R XOR Error 가 됨
        codeword_noisy = xor_bytes(helper, biometric_noisy)

        # 3. 디코딩 (오류 정정)
        try:
            # 여기서 64비트 이하의 오류가 있다면 정정되어 원본 Secret Message가 반환됨
            recovered_secret = self.codec.decode(codeword_noisy)
            return recovered_secret
        except RuntimeError:
            # 복원 실패 (오류가 허용 범위를 초과함)
            return None
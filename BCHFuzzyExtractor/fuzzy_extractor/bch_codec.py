import galois
import numpy as np


class BCHCodec:
    def __init__(self, t=64, m=13):
        """
        BCH 코덱 초기화 (galois 라이브러리 사용)
        :param t: 허용 가능한 오류 비트 수 (기본 64)
        :param m: 갈루아 필드 차원 (기본 13 -> n=8191)
        """
        self.t = t
        self.m = m
        self.n = 2 ** m - 1  # 8191

        # 공식: d = 2 * t + 1
        design_distance = 2 * t + 1

        try:
            print(f"[Info] BCH 코드를 생성합니다 (n={self.n}, t={t}, d={design_distance})...")
            # primitive_poly는 자동으로 최적값을 찾습니다.
            self.bch = galois.BCH(self.n, d=design_distance)
        except Exception as e:
            raise RuntimeError(f"BCH 초기화 실패: {e}")

        # 정보 비트의 길이 (k)
        self.k = self.bch.k

        # 전체 허용 가능한 바이트 길이 (n 비트 기준)
        # 3488비트(436바이트)만 사용
        self.total_target_bytes = 436

        # ECC 비트 수
        self.ecc_bits = self.n - self.k

        # ECC 바이트 수
        self.ecc_bytes = (self.ecc_bits + 7) // 8

        # 실제 데이터 바이트 수
        self.data_bytes = self.total_target_bytes - self.ecc_bytes

        print(f"[Info] 설정 완료: Total={self.total_target_bytes}B, Data={self.data_bytes}B, ECC={self.ecc_bytes}B")

        if self.data_bytes <= 0:
            raise ValueError("오류 정정 비트가 너무 커서 데이터를 담을 공간이 없습니다.")

    def encode(self, data):
        """
        Bytes 데이터 -> Bit Array 변환 -> BCH 인코딩 -> Bytes 반환
        """
        if len(data) > self.data_bytes:
            raise ValueError(f"데이터가 너무 큽니다. (최대 {self.data_bytes} bytes)")

        # 1. 패딩
        if len(data) < self.data_bytes:
            data = data.ljust(self.data_bytes, b'\0')

        # 2. Bytes -> Bit Array (GF2)
        # numpy를 이용해 바이트를 비트 배열로 변환
        data_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        gf_data = galois.GF2(data_bits)

        # 3. 인코딩 (Encode)
        codeword_gf = self.bch.encode(gf_data)

        # [수정] FieldArray를 일반 numpy 배열로 변환 후 packbits 수행
        codeword_array = codeword_gf.view(np.ndarray).astype(np.uint8)

        # 4. Bit Array -> Bytes 변환
        codeword_bytes = np.packbits(codeword_array).tobytes()

        # 5. 길이 맞춤 (Shortening)
        return codeword_bytes[:self.total_target_bytes]

    def decode(self, packet):
        """
        Bytes 패킷 -> Bit Array -> BCH 디코딩 -> Bytes 반환
        """
        if len(packet) != self.total_target_bytes:
            pass

            # 1. Bytes -> Bit Array (GF2)
        packet_bits = np.unpackbits(np.frombuffer(packet, dtype=np.uint8))

        # 2. Shortening 복원
        pad_len = self.n - len(packet_bits)
        if pad_len > 0:
            packet_bits = np.pad(packet_bits, (0, pad_len), 'constant')

        gf_packet = galois.GF2(packet_bits)

        # 3. 디코딩 (Decode)
        try:
            decoded_gf = self.bch.decode(gf_packet)

            # [수정] FieldArray를 일반 numpy 배열로 변환 후 packbits 수행
            decoded_array = decoded_gf.view(np.ndarray).astype(np.uint8)

            # 4. 결과 변환
            decoded_bytes = np.packbits(decoded_array).tobytes()

            return decoded_bytes[:self.data_bytes]

        except Exception:
            raise RuntimeError("오류가 너무 많아 복원할 수 없습니다.")
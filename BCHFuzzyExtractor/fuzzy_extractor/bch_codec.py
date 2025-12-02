import galois
import numpy as np


class BCHCodec:
    def __init__(self, t=64, m=13):
        self.t = t
        self.m = m
        self.n = 2 ** m - 1  # 8191

        design_distance = 2 * t + 1

        try:
            print(f"[Info] BCH 코드를 생성합니다 (n={self.n}, t={t})...")
            self.bch = galois.BCH(self.n, d=design_distance)
        except Exception as e:
            raise RuntimeError(f"BCH 초기화 실패: {e}")

        self.k = self.bch.k  # 메시지 블록 크기
        self.ecc_bits = self.n - self.k  # ECC 패리티 크기

        # 목표: 3488비트 (436바이트)
        self.total_target_bits = 3488
        self.total_target_bytes = 436

        # 실제 데이터가 들어갈 비트 수
        self.data_bits = self.total_target_bits - self.ecc_bits
        self.data_bytes = (self.data_bits + 7) // 8

        print(
            f"[Info] 설정: Total={self.total_target_bits}bits, Data Space={self.data_bits}bits, ECC={self.ecc_bits}bits")

        if self.data_bits <= 0:
            raise ValueError("오류 정정 비트가 너무 커서 데이터를 담을 공간이 없습니다.")

    def encode(self, data):
        """
        [Left Padding 적용]
        Zeros를 왼쪽에 채워서 인코딩 후, 앞부분 Zeros를 제거하고 반환
        """
        # 1. 바이트 -> 비트 변환
        data_arr = np.frombuffer(data, dtype=np.uint8)
        data_bits = np.unpackbits(data_arr)

        if len(data_bits) > self.data_bits:
            data_bits = data_bits[:self.data_bits]

        # 2. Shortening (앞쪽에 0 추가)
        pad_len = self.k - len(data_bits)
        msg_bits = np.pad(data_bits, (pad_len, 0), 'constant')  # (앞, 뒤)

        gf_msg = galois.GF2(msg_bits)

        # 3. 인코딩 -> [Zeros | Data | Parity]
        codeword_gf = self.bch.encode(gf_msg)

        # 4. 앞쪽 Zeros 제거 -> [Data | Parity]
        shortened_codeword_gf = codeword_gf[pad_len:]

        # 5. 비트 -> 바이트 변환
        codeword_array = shortened_codeword_gf.view(np.ndarray).astype(np.uint8)
        codeword_bytes = np.packbits(codeword_array).tobytes()

        return codeword_bytes

    def decode(self, packet):
        """
        [Left Padding 복원]
        앞에 0을 붙여서 디코딩한 후, 결과(Zeros | Data)에서 앞쪽 Zeros를 건너뛰고 Data만 취함
        """
        # 1. 바이트 -> 비트 변환
        packet_arr = np.frombuffer(packet, dtype=np.uint8)
        packet_bits = np.unpackbits(packet_arr)

        if len(packet_bits) > self.total_target_bits:
            packet_bits = packet_bits[:self.total_target_bits]

        # 2. Shortening 복원 (앞쪽에 0 추가하여 원래 길이 8191 맞춤)
        pad_len = self.n - len(packet_bits)
        full_codeword_bits = np.pad(packet_bits, (pad_len, 0), 'constant')

        gf_packet = galois.GF2(full_codeword_bits)

        try:
            # 3. 디코딩 -> [Zeros | Data] 가 나옴
            decoded_gf = self.bch.decode(gf_packet)

            # [핵심 수정] 앞쪽 패딩 제거 (Slicing)
            # 메시지 블록(k) 안에서 데이터 앞에 0이 몇 개 있었는지 계산
            msg_pad_len = self.k - self.data_bits

            # 0들을 건너뛰고(skip) 뒤의 데이터만 가져옴
            real_data_gf = decoded_gf[msg_pad_len:]

            # 5. 비트 -> 바이트 변환
            data_array = real_data_gf.view(np.ndarray).astype(np.uint8)
            return np.packbits(data_array).tobytes()

        except Exception:
            raise RuntimeError("오류가 너무 많아 복원할 수 없습니다.")

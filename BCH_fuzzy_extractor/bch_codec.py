import galois
import numpy as np


class BCHCodec:
    def __init__(self, t=64, m=13):
        self.t = t
        self.m = m
        self.n = 2 ** m - 1  # 8191

        design_distance = 2 * t + 1

        try:
            print(f"[Info] Initializing BCH code (n={self.n}, t={t})...")
            self.bch = galois.BCH(self.n, d=design_distance)
        except Exception as e:
            raise RuntimeError(f"BCH initialization failed: {e}")

        self.k = self.bch.k  # message block size
        self.ecc_bits = self.n - self.k  # ECC parity bits

        # Target: 3488 bits
        self.total_target_bits = 3488
        self.total_target_bytes = 436

        # Number of bits available for data
        self.data_bits = self.total_target_bits - self.ecc_bits
        self.data_bytes = (self.data_bits + 7) // 8

        print(
            f"[Info] Config: Total={self.total_target_bits}bits, Data Space={self.data_bits}bits, ECC={self.ecc_bits}bits")

        if self.data_bits <= 0:
            raise ValueError("Error-correction parity is too large; no room for data.")

    def encode(self, data):
        # 1. bytes -> bits
        data_arr = np.frombuffer(data, dtype=np.uint8)
        data_bits = np.unpackbits(data_arr)

        if len(data_bits) > self.data_bits:
            data_bits = data_bits[:self.data_bits]

        # 2. Shortening
        pad_len = self.k - len(data_bits)
        msg_bits = np.pad(data_bits, (pad_len, 0), 'constant')  # (front, back)

        gf_msg = galois.GF2(msg_bits)

        # 3. Encode -> [Zeros | Data | Parity]
        codeword_gf = self.bch.encode(gf_msg)

        # 4. Remove leading zeros -> [Data | Parity]
        shortened_codeword_gf = codeword_gf[pad_len:]

        # 5. bits -> bytes
        codeword_array = shortened_codeword_gf.view(np.ndarray).astype(np.uint8)
        codeword_bytes = np.packbits(codeword_array).tobytes()

        return codeword_bytes

    def decode(self, packet):
        # 1. bytes -> bits
        packet_arr = np.frombuffer(packet, dtype=np.uint8)
        packet_bits = np.unpackbits(packet_arr)

        if len(packet_bits) > self.total_target_bits:
            packet_bits = packet_bits[:self.total_target_bits]

        # 2. Restore shortening
        pad_len = self.n - len(packet_bits)
        full_codeword_bits = np.pad(packet_bits, (pad_len, 0), 'constant')

        gf_packet = galois.GF2(full_codeword_bits)

        try:
            # 3. Decode -> returns [Zeros | Data]
            decoded_gf = self.bch.decode(gf_packet)

            # Remove leading padding
            # Compute how many zeros were at the front inside the message block (k)
            msg_pad_len = self.k - self.data_bits

            # Skip the zeros and take the following data bits
            real_data_gf = decoded_gf[msg_pad_len:]

            # 5. bits -> bytes
            data_array = real_data_gf.view(np.ndarray).astype(np.uint8)
            return np.packbits(data_array).tobytes()

        except Exception:
            raise RuntimeError("Too many errors to recover the message.")

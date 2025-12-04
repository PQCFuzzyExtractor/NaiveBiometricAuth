# Bio-Key Extraction with Fuzzy Extractor using BCH

이 프로젝트는 생체 정보(Biometric Data)를 이용하여 암호화 키를 안전하게 생성하고 복구하는 **Fuzzy Extractor** 구현체입니다.
Post-Quantum Cryptography (Classic McEliece)와의 연동을 위해 **3488비트 입력 벡터**와 **64비트 오류 정정(Error Correction)**을 지원하도록 설계되었습니다.

## 📌 Key Features
- **Algorithm:** Code Offset Construction
- **Error Correction:** BCH Code (Shortened to 3488 bits input)
- **Parameters:**
  - Input Dimension: 3488 bits (436 bytes)
  - Error Tolerance: Up to 64 bits (Hamming Distance)
  - Field Size: $m=13$ (Galois Field $2^{13}$)
- **Library:** Uses `galois` library for Python-based finite field arithmetic.

## 📂 Project Structure
```text
fuzzy_extractor/
├── bch_codec.py       # BCH Encoder/Decoder Implementation
├── fuzzy_extractor.py # Fuzzy Extractor Logic (Gen/Rep)
├── storage.py         # Helper Data Storage (SQLite)
└── utils.py           # Bitwise Operations & Hashing
test_simulation.py     # Scenario Test Code
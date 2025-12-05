# NaiveBiometricAuth  
Iris Feature Extraction Module (ArcFace + CNN)

본 모듈은 홍채 이미지로부터 3488bit Iris Code를 생성하고,
두 Iris Code 간의 Hamming Distance를 계산하는 기능을 제공합니다.

## Directory Structure
```text
feature-extraction-module/
 ├── arcface_backbone.py        # ArcFace 기반 CNN 백본  
 ├── extract_feature_arcface.py # 메인 실행/테스트용 스크립트  
 ├── utils.py                    # 공용 유틸(Hamming, seed 등)  
 ├── checkpoints/  
 │     └── arcface_backbone.pth # 학습된 백본 모델  
 ├── samples/  
       └── S5000L00.jpg         # 테스트 이미지  
```
## Features
1. 3488-dim Iris Embedding (CNN ArcFace)

ArcFace 기반 CNN 모델을 로딩하여
입력 이미지에서 3488차원 float embedding을 생성합니다.

2. Binary Iris Code (3488bit)

float embedding을
sign(x) > 0 → 1, else → 0
규칙으로 이진화하여 IrisCode를 생성합니다.

3. Hamming Distance 계산

3488bit iris code 두 개를 입력받아
비트 차이를 계산합니다.

4. API 함수 제공

다음 두 함수가 외부 서비스에서 호출할 핵심 API입니다:

``` python
extract_iris_code(image_path) → binary_iris_code(0/1, 3488bit)
compare_iris_codes(code1, code2) → hamming_distance(int)
```
## Installation
``` python
pip install torch torchvision numpy pillow
```

## Run Example

샘플 이미지로 특징 벡터 추출:
``` bash
python extract_feature_arcface.py --image samples/S5000L00.jpg
```

출력 예시:
``` bash
Binary iris code shape: (3488,)
First 32 bits: [0 0 1 0 0 0 0 1 0 ...]
```
## API Usage
IrisCode 생성
``` python
from extract_feature_arcface import extract_iris_code

code = extract_iris_code("samples/S5000L00.jpg")
print(code.shape)   # (3488,)
```
Hamming Distance
``` python
from extract_feature_arcface import compare_iris_codes

dist = compare_iris_codes(code_A, code_B)
print("HD =", dist)
```
## Notes

CNN 모델은 ArcFace Loss 기반으로 학습됨

3488bit IrisCode는 CNN feature를 이진화한 형태이며
정책 기준(Hamming Threshold)는 시스템에서 설정 가능

전통적 Daugman IrisCode의 64bit 기준과는 다름

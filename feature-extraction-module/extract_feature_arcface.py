# extract_feature_arcface.py
import torch
import numpy as np
from PIL import Image
from torchvision import transforms

from arcface_backbone import ArcFaceBackbone

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_PATH = "checkpoints/arcface_backbone.pth"


# -----------------------------
# 1) 이미지 전처리 함수
# -----------------------------
def preprocess_image(image_path):
    img = Image.open(image_path).convert("L")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.expand(3, -1, -1)),  # 1→3 채널 확장
    ])
    return transform(img).unsqueeze(0).to(DEVICE)


# -----------------------------
# 2) float → binary 이진화
# -----------------------------
def float_to_binary(feature: np.ndarray):
    return (feature >= 0).astype(np.uint8)   # 0 또는 1


# -----------------------------
# 3) 모델 로드
# -----------------------------
def load_backbone():
    model = ArcFaceBackbone().to(DEVICE)
    state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model.eval()
    return model


# -----------------------------
# ⭐ 함수 A: iris code 추출
# -----------------------------
def extract_iris_code(image_path):
    model = load_backbone()
    img = preprocess_image(image_path)

    with torch.no_grad():
        embedding = model(img).cpu().numpy().flatten()   # float 3488

    binary_code = float_to_binary(embedding)  # 3488-bit
    return binary_code


# -----------------------------
# ⭐ 함수 B: 두 이미지 비교
# -----------------------------
def hamming_distance(code1, code2):
    return int(np.sum(code1 != code2))


def compare_iris(image_a, image_b):
    code1 = extract_iris_code(image_a)
    code2 = extract_iris_code(image_b)

    hd = hamming_distance(code1, code2)
    same_person = (hd <= 64)

    return {
        "hamming_distance": hd,
        "same_person": same_person
    }


# -----------------------------
# CLI 테스트용
# -----------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, required=True)
    args = parser.parse_args()

    code = extract_iris_code(args.image)
    print(f"Binary iris code shape: {code.shape}")
    print(f"First 32 bits: {code[:32]}")

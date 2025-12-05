# extract_feature_arcface.py
import os

import torch
import numpy as np
from PIL import Image
from torchvision import transforms

from feature_extraction_module.arcface_backbone import ArcFaceBackbone
from feature_extraction_module.utils import set_seed as utils_set_seed

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "checkpoints", "arcface_backbone.pth")


# -----------------------------
# global model variable (lazy load)
# -----------------------------
_MODEL = None
_MODEL_PATH = MODEL_PATH
_DEVICE = DEVICE


# -----------------------------
# 1) Image Post-processing Function
# -----------------------------
def preprocess_image(image_path):
    img = Image.open(image_path).convert("L")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x.expand(3, -1, -1)),  # 1→3 채널 확장
    ])
    return transform(img).unsqueeze(0).to(_DEVICE)


# -----------------------------
# 2) float → binary Transform
# -----------------------------
def float_to_binary(feature: np.ndarray):
    arr = (feature >= 0).astype(np.uint8)
    return arr.reshape(-1)


# -----------------------------
# 3) Model Load / Init Functions
# -----------------------------
def load_backbone(model_path, device):
    model = ArcFaceBackbone().to(device)
    if os.path.exists(model_path):
        try:
            state_dict = torch.load(model_path, map_location=device)
            model.load_state_dict(state_dict)
            model.eval()
            print(f"[INFO] Loaded backbone from `{model_path}`")
            return model
        except Exception as e:
            print(f"[WARN] CheckPoint Load Failed: {e} — Continuing with random weights.")
            model.eval()
            return model
    else:
        print(f"[WARN] Checkpoint `{model_path}` doesn't exist. Continuing with random weights.")
        model.eval()
        return model


def init_model(seed: int = 42, model_path: str = None, device: str = None):
    global _MODEL, _MODEL_PATH, _DEVICE
    if model_path:
        _MODEL_PATH = model_path
    if device:
        _DEVICE = device

    # set seed
    utils_set_seed(seed)

    # load model
    _MODEL = load_backbone(_MODEL_PATH, _DEVICE)


# -----------------------------
# iris code Extraction
# -----------------------------
def extract_iris_code(image_path):
    global _MODEL
    if _MODEL is None:
        init_model(42)

    img = preprocess_image(image_path)

    with torch.no_grad():
        embedding = _MODEL(img).cpu().numpy().flatten()   # float 3488

    binary_code = float_to_binary(embedding)  # 3488-bit
    return binary_code


# -----------------------------
# Compare Two iris-codes
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

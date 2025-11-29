# utils.py
import os
import torch
import numpy as np
import random
import torch.backends.cudnn as cudnn


# -------------------------------------------------------
# 1) Reproducibility
# -------------------------------------------------------
def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    cudnn.deterministic = True
    cudnn.benchmark = False

    print(f"[INFO] Seed fixed to {seed}")


# -------------------------------------------------------
# 2) Save / Load Model
# -------------------------------------------------------
def save_model(model, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)
    print(f"[INFO] Model saved to {path}")


def load_model(model_class, path: str, device="cpu", **kwargs):
    """
    model_class: class object (e.g. IrisNet)
    **kwargs: parameters passed to model_class (e.g. out_dim=3488)
    """
    model = model_class(**kwargs).to(device)

    state_dict = torch.load(path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()

    print(f"[INFO] Loaded model from {path}")
    return model


# -------------------------------------------------------
# 3) Binary Encode (Convert float embedding → 0/1 iris code)
# -------------------------------------------------------
def binary_encode(embedding_tensor: torch.Tensor, threshold: float = 0.0):
    """
    embedding_tensor: tensor shape (B, D)
    Returns numpy binary array (B, D) with values {0,1}
    """
    if embedding_tensor.dim() != 2:
        raise ValueError("binary_encode expects (B, D) tensor.")

    binary = (embedding_tensor > threshold).int().cpu().numpy()
    return binary


# -------------------------------------------------------
# 4) Hamming Distance
# -------------------------------------------------------
def hamming_distance(v1: np.ndarray, v2: np.ndarray) -> int:
    """
    v1, v2: numpy arrays of shape (D,)
    """
    if v1.shape != v2.shape:
        raise ValueError(f"Hamming distance mismatch: {v1.shape} vs {v2.shape}")

    return int(np.sum(v1 != v2))

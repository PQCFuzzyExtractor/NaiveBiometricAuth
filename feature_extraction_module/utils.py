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
    embedding_tensor: tensor of shape (B, D) or (D,)
    Returns numpy binary array of shape (B, D) with values {0,1}
    If a 1D tensor is provided, it is treated as a batch of size 1.
    """
    if embedding_tensor.dim() == 1:
        embedding_tensor = embedding_tensor.unsqueeze(0)
    elif embedding_tensor.dim() != 2:
        raise ValueError("binary_encode expects a tensor of shape (B, D) or (D,).")

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

# -------------------------------------------------------
# 5) Iris Code to Bytes Conversion
# -------------------------------------------------------
def iris_code_to_bytes(code_array: np.ndarray) -> bytes:
    if code_array.dtype != np.uint8:
        code_array = code_array.astype(np.uint8)
    packed = np.packbits(code_array)  # length should be 436
    if len(packed) != 436:
        raise ValueError(f"Packed length mismatch: {len(packed)} != 436")
    return packed.tobytes()
import torch
import torch.nn as nn
from torchvision.models import mobilenet_v2


class ArcFaceBackbone(nn.Module):
    """
    ArcFace 학습에서 사용한 MobilenetV2 기반 백본.
    최종 feature_dim = 3488 으로 고정.
    """
    def __init__(self, feature_dim=3488):
        super().__init__()

        # 1) Pretrained backbone
        m = mobilenet_v2(weights=None)

        # 2) 마지막 classifier 제거
        self.feature_extractor = nn.Sequential(*list(m.features))

        # 3) Adaptive pooling
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

        # 4) Embedding layer (ArcFace와 동일한 구조)
        self.fc = nn.Linear(1280, feature_dim)

    def forward(self, x):
        x = self.feature_extractor(x)   # (B,1280,H,W)
        x = self.pool(x)                # (B,1280,1,1)
        x = x.view(x.size(0), -1)       # (B,1280)
        x = self.fc(x)                  # (B,3488)
        return x

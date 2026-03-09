"""Image transforms for UniPCB dataset."""

from typing import Optional, Tuple
import albumentations as A
from albumentations.pytorch import ToTensorV2


def get_transform(
    image_size: Tuple[int, int] = (224, 224),
    is_training: bool = True,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225),
) -> A.Compose:
    """
    获取图像变换。
    
    Args:
        image_size: 目标图像尺寸
        is_training: 是否为训练模式
        mean: 归一化均值
        std: 归一化标准差
    
    Returns:
        albumentations 变换组合
    """
    if is_training:
        return A.Compose([
            A.RandomResizedCrop(height=image_size[0], width=image_size[1], scale=(0.8, 1.0)),
            A.HorizontalFlip(p=0.5),
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.5),
            A.Normalize(mean=mean, std=std),
            ToTensorV2(),
        ])
    else:
        return A.Compose([
            A.Resize(height=image_size[0], width=image_size[1]),
            A.Normalize(mean=mean, std=std),
            ToTensorV2(),
        ])

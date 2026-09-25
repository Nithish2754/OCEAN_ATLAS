from __future__ import annotations

import cv2
import numpy as np


def apply_underwater_color_correction(frame_bgr: np.ndarray) -> np.ndarray:
    """Apply a simple gray-world color correction to compensate for underwater blue/green cast."""
    img = frame_bgr.astype(np.float32)
    channel_means = img.mean(axis=(0, 1))
    target = float(channel_means.mean())
    gains = np.clip(target / np.maximum(channel_means, 1e-6), 0.5, 3.0)
    corrected = img * gains
    corrected = np.clip(corrected, 0, 255)
    return corrected.astype(np.uint8)


def preprocess_frame(
    frame: np.ndarray,
    resize_shape: tuple[int, int] = (224, 224),
    denoise_h: float = 10.0,
    denoise_color_h: float = 10.0,
) -> np.ndarray:
    """Apply the full underwater preprocessing pipeline used in training and inference."""
    if frame is None or frame.size == 0:
        raise ValueError("Received an empty image frame for preprocessing.")

    image = frame.copy()
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    corrected = apply_underwater_color_correction(image)

    lab = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB).astype(np.float32)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_equalized = clahe.apply(l_channel.astype(np.uint8))
    lab_equalized = cv2.merge([l_equalized, a_channel.astype(np.uint8), b_channel.astype(np.uint8)])

    bgr_equalized = cv2.cvtColor(lab_equalized, cv2.COLOR_LAB2BGR)
    denoised = cv2.fastNlMeansDenoisingColored(
        bgr_equalized,
        None,
        h=denoise_h,
        hColor=denoise_color_h,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    resized = cv2.resize(denoised, resize_shape)
    return resized.astype(np.uint8)

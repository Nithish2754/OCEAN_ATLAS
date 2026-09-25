import cv2
import numpy as np

from oceanatlas.preprocessing import preprocess_frame
from oceanatlas.features import extract_frame_features, build_visual_payload
from oceanatlas.realtime import detect_sample_presence, majority_vote_label


def test_preprocess_frame_returns_valid_image():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    frame[50:150, 80:240] = (20, 40, 90)

    processed = preprocess_frame(frame, resize_shape=(224, 224))

    assert processed.shape == (224, 224, 3)
    assert processed.dtype == np.uint8
    assert processed.min() >= 0
    assert processed.max() <= 255


def test_preprocess_frame_accepts_lighter_texture_preserving_denoising():
    frame = np.random.default_rng(42).integers(0, 256, (64, 64, 3), dtype=np.uint8)

    processed = preprocess_frame(frame, resize_shape=(64, 64), denoise_h=3, denoise_color_h=3)

    assert processed.shape == frame.shape
    assert processed.dtype == np.uint8


def test_extract_frame_features_returns_vector():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    frame[:, :, 0] = 90
    frame[:, :, 1] = 80
    frame[:, :, 2] = 70

    vector = extract_frame_features(frame)

    assert isinstance(vector, np.ndarray)
    assert vector.ndim == 1
    assert vector.size > 0


def test_visual_payload_uses_allowed_classes_only():
    payload = build_visual_payload("cobalt_rich_crust", 0.61)

    assert payload["visual_class"] == "cobalt_rich_crust"
    assert "cobalt" in payload["message"].lower()
    assert "sediment" not in payload["message"].lower()


def test_detect_sample_presence_flags_empty_background():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    empty, box = detect_sample_presence(frame, min_area=5000)

    assert empty is True
    assert box is None


def test_majority_vote_label_uses_consensus():
    labels = [
        "polymetallic_nodules",
        "polymetallic_nodules",
        "hydrothermal_sulphides",
        "polymetallic_nodules",
        "polymetallic_nodules",
    ]

    assert majority_vote_label(labels) == "polymetallic_nodules"


def test_headless_display_helpers_gracefully_handle_gui_error(monkeypatch):
    from oceanatlas.live_pipeline import _safe_imshow, _safe_wait_key

    def raise_error(*_args, **_kwargs):
        raise cv2.error("No GUI backend")

    monkeypatch.setattr(cv2, "imshow", raise_error)
    monkeypatch.setattr(cv2, "waitKey", raise_error)

    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    assert _safe_imshow("OceanAtlas", frame) is False
    assert _safe_wait_key(1) == -1


def test_yolo_detection_schema_uses_only_three_classes():
    from oceanatlas.yolo_pipeline import YOLO_CLASS_NAMES, build_detection_payload

    assert YOLO_CLASS_NAMES == [
        "polymetallic_nodules",
        "cobalt_rich_crust",
        "hydrothermal_sulphide",
    ]

    payload = build_detection_payload(
        device_id="ROV-3-CAM",
        detections=[
            {"class": "polymetallic_nodules", "confidence": 0.88, "bbox": [10, 20, 30, 40]},
            {"class": "cobalt_rich_crust", "confidence": 0.71, "bbox": [50, 60, 70, 80]},
        ],
    )

    assert payload["device_id"] == "ROV-3-CAM"
    assert payload["detections"][0]["class"] in YOLO_CLASS_NAMES
    assert len(payload["detections"]) == 2

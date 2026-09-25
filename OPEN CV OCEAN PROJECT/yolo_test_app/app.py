from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
import streamlit as st
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = "runs/detect/runs/detect-3/weights/best.pt"
IMAGE_SIZE = 640
EXPECTED_CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]
FRIENDLY_CLASS_NAMES = {
    "polymetallic_nodules": "Polymetallic Nodules",
    "cobalt_rich_crust": "Cobalt-Rich Crust",
    "hydrothermal_sulphide": "Hydrothermal Sulphide",
}
EXPECTED_OPTIONS = [
    "Polymetallic Nodules",
    "Cobalt-Rich Crust",
    "Hydrothermal Sulphide",
    "Any Deposit",
]
EXPECTED_OPTION_TO_CLASS = {
    "Polymetallic Nodules": "polymetallic_nodules",
    "Cobalt-Rich Crust": "cobalt_rich_crust",
    "Hydrothermal Sulphide": "hydrothermal_sulphide",
    "Any Deposit": "any_deposit",
}
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


@st.cache_resource(show_spinner=False)
def load_model(model_path: str) -> YOLO:
    resolved_path = (PROJECT_ROOT / model_path).resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Model not found at: {resolved_path}")

    model = YOLO(str(resolved_path))
    try:
        device = "cuda" if __import__("torch").cuda.is_available() else "cpu"
        model.to(device)
    except Exception:
        model.to("cpu")
    return model


def verify_model_class_mapping(model: YOLO) -> tuple[bool, list[str]]:
    names = getattr(model, "names", {}) or {}
    if not names:
        return False, []

    resolved_names = [str(names.get(index, "")) for index in range(len(names))]
    expected = EXPECTED_CLASS_NAMES.copy()
    return resolved_names == expected, resolved_names


def get_expected_class_value(selected_label: str) -> str | None:
    if selected_label == "Any Deposit":
        return "any_deposit"
    return EXPECTED_OPTION_TO_CLASS.get(selected_label)


def _load_image_from_upload(file) -> np.ndarray:
    if file is None:
        raise ValueError("No image file was uploaded.")

    image_bytes = file.read()
    if not image_bytes:
        raise ValueError("Uploaded image is empty.")

    try:
        image = np.array(Image.open(file).convert("RGB"))
    except UnidentifiedImageError as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc
    except Exception as exc:
        raise ValueError("Unable to open the uploaded image.") from exc

    if image.size == 0:
        raise ValueError("The uploaded image is blank.")

    return image


def normalize_detections(raw_detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for detection in raw_detections:
        class_name = str(detection.get("class", "unknown"))
        confidence = float(detection.get("confidence", 0.0))
        bbox = detection.get("bbox", [0, 0, 0, 0])
        normalized.append({
            "class": class_name,
            "confidence": confidence,
            "bbox": bbox,
        })
    return sorted(normalized, key=lambda item: item["confidence"], reverse=True)


def run_yolo_on_image(model: YOLO, image: np.ndarray, conf_threshold: float) -> list[dict[str, Any]]:
    results = model(image, conf=conf_threshold, imgsz=IMAGE_SIZE, verbose=False)
    detections: list[dict[str, Any]] = []

    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            continue

        names = getattr(model, "names", {}) or {}
        for box in boxes:
            cls_index = int(box.cls.item())
            class_name = str(names.get(cls_index, f"class_{cls_index}"))
            confidence = float(box.conf.item())
            x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
            width = max(0.0, x2 - x1)
            height = max(0.0, y2 - y1)
            detections.append({
                "class": class_name,
                "confidence": confidence,
                "bbox": [x1, y1, width, height],
            })

    return normalize_detections(detections)


def draw_boxes(image: np.ndarray, detections: list[dict[str, Any]]) -> np.ndarray:
    result_image = image.copy()
    if not detections:
        return result_image

    for index, detection in enumerate(detections):
        x, y, width, height = detection["bbox"]
        class_name = detection["class"]
        confidence = detection["confidence"]
        x1 = int(round(x))
        y1 = int(round(y))
        x2 = int(round(x + width))
        y2 = int(round(y + height))

        color_map = {
            "polymetallic_nodules": (0, 255, 0),
            "cobalt_rich_crust": (0, 165, 255),
            "hydrothermal_sulphide": (255, 0, 0),
        }
        color = color_map.get(class_name, (255, 255, 255))
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
        label = f"{class_name} {confidence:.2f}"
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(result_image, (x1, max(0, y1 - 22)), (x1 + text_w + 8, max(0, y1)), color, -1)
        cv2.putText(result_image, label, (x1 + 4, max(12, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        if index == 0:
            cv2.putText(
                result_image,
                "YOLO DETECTION",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
    return result_image


def evaluate_model_test(expected_class: str | None, filtered_detections: list[dict[str, Any]]) -> tuple[str, str, str | None]:
    if not filtered_detections:
        return "FAIL", "MODEL TEST: FAIL", None

    if expected_class in {"any_deposit", None}:
        return "PASS", "MODEL TEST: PASS", filtered_detections[0]["class"]

    detected_classes = {entry["class"] for entry in filtered_detections}
    if expected_class in detected_classes:
        return "PASS", "MODEL TEST: PASS", expected_class

    if detected_classes:
        first_detected = sorted(filtered_detections, key=lambda item: item["confidence"], reverse=True)[0]["class"]
        return "WRONG CLASS", "MODEL TEST: WRONG CLASS", first_detected

    return "FAIL", "MODEL TEST: FAIL", None


def render_single_image_test() -> None:
    st.title("OceanAtlas - YOLO Model Tester")
    st.caption("Test whether the current YOLO model can detect underwater metal deposits from an uploaded image.")

    with st.form("yolo_test_form"):
        uploaded_file = st.file_uploader(
            "Upload Test Image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload one image to test the current YOLO model.",
        )
        expected_deposit = st.selectbox(
            "Expected Deposit Type",
            EXPECTED_OPTIONS,
            index=3,
        )
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.05,
            max_value=0.95,
            value=0.25,
            step=0.05,
        )
        run_detection = st.form_submit_button("Run YOLO Detection")

    if not run_detection:
        return

    if uploaded_file is None:
        st.error("Please upload an image before running detection.")
        return

    file_extension = Path(uploaded_file.name).suffix.lower().lstrip(".")
    if file_extension not in ALLOWED_EXTENSIONS:
        st.error("Unsupported image format. Use JPG, JPEG, PNG, or WEBP.")
        return

    try:
        image = _load_image_from_upload(uploaded_file)
    except ValueError as exc:
        st.error(str(exc))
        return

    st.subheader("ORIGINAL IMAGE")
    st.image(image, caption="Uploaded image", use_container_width=True)

    model_path = str((PROJECT_ROOT / MODEL_PATH).resolve())
    st.subheader("MODEL DIAGNOSTICS")
    st.write(f"Model: {model_path}")

    try:
        model = load_model(MODEL_PATH)
    except FileNotFoundError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Model loading error: {exc}")
        return

    class_map_ok, class_names = verify_model_class_mapping(model)
    diagnostic_classes = class_names if class_names else list(model.names.values()) if getattr(model, "names", None) else []
    st.write(f"Model classes: {diagnostic_classes}")
    st.write(f"Image size: {IMAGE_SIZE}")
    st.write(f"Confidence threshold: {confidence_threshold:.2f}")

    if not class_map_ok:
        st.warning(
            "The loaded YOLO model class mapping does not match the expected OceanAtlas classes: "
            f"{EXPECTED_CLASS_NAMES}. The app will not silently change the class mapping."
        )

    expected_class = get_expected_class_value(expected_deposit)
    raw_predictions = run_yolo_on_image(model, image, conf_threshold=0.0)
    filtered_predictions = [d for d in raw_predictions if d["confidence"] >= confidence_threshold]

    st.subheader("YOLO RAW PREDICTIONS")
    if not raw_predictions:
        st.write("YOLO RAW PREDICTIONS: No detections returned by the model.")
    else:
        for index, detection in enumerate(raw_predictions, start=1):
            bbox = detection["bbox"]
            st.write(
                f"Detection {index}: Class: {detection['class']}; "
                f"Confidence: {detection['confidence']:.2f}; "
                f"Bounding Box: x={bbox[0]:.0f}, y={bbox[1]:.0f}, width={bbox[2]:.0f}, height={bbox[3]:.0f}"
            )

    st.subheader("FILTERED PREDICTIONS")
    if not filtered_predictions:
        st.write("No detections passed the confidence threshold.")
    else:
        for index, detection in enumerate(filtered_predictions, start=1):
            bbox = detection["bbox"]
            st.write(
                f"Detection {index}: Class: {detection['class']}; "
                f"Confidence: {detection['confidence']:.2f}; "
                f"Bounding Box: x={bbox[0]:.0f}, y={bbox[1]:.0f}, width={bbox[2]:.0f}, height={bbox[3]:.0f}"
            )

    st.subheader("RESULT")
    result_status, result_label, best_class = evaluate_model_test(expected_class, filtered_predictions)
    st.markdown(f"### {result_label}")

    if filtered_predictions:
        top_detection = filtered_predictions[0]
        if expected_class in {"any_deposit", None}:
            expected_display = "Any Deposit"
        else:
            expected_display = FRIENDLY_CLASS_NAMES.get(expected_class, expected_class)
        detected_display = FRIENDLY_CLASS_NAMES.get(top_detection["class"], top_detection["class"])
        st.write(f"Detected Type: {detected_display}")
        st.write(f"Confidence: {top_detection['confidence'] * 100:.0f}%")
        st.write(f"Number of detections: {len(filtered_predictions)}")

        if expected_class not in {"any_deposit", None}:
            if top_detection["class"] == expected_class:
                st.success(f"PASS\nExpected: {expected_display}\nDetected: {detected_display}\nConfidence: {top_detection['confidence'] * 100:.0f}%")
            else:
                st.warning(f"WRONG CLASS\nExpected: {expected_display}\nDetected: {detected_display}")
    else:
        st.write("No accepted detection at the selected threshold.")

    st.subheader("YOLO DETECTION RESULT")
    if filtered_predictions:
        box_image = draw_boxes(image, filtered_predictions)
        st.image(box_image, caption="YOLO detection result", use_container_width=True)
    else:
        st.image(image, caption="No YOLO detections.", use_container_width=True)

    st.subheader("MODEL TEST")
    if result_status == "PASS":
        st.success("MODEL TEST: PASS\nThe current YOLO model successfully detected the expected deposit in the uploaded image.")
    elif result_status == "WRONG CLASS":
        st.warning("MODEL TEST: WRONG CLASS\nThe YOLO model detected an object but classified it as the wrong deposit type.\nRecommendation: Improve class-specific training data and annotations.")
    else:
        st.error("MODEL TEST: FAIL\nThe current YOLO model did not detect the uploaded deposit image.\nRecommendation: Improve/retrain the YOLO model and dataset.")

    st.markdown("---")
    st.write(f"Number of raw detections: {len(raw_predictions)}")
    st.write(f"Number of accepted detections: {len(filtered_predictions)}")
    st.write(f"Expected class: {expected_deposit}")
    st.write(f"Best detection: {best_class if best_class else 'none'}")

    st.markdown("---")
    st.markdown("#### Final diagnostic interpretation")
    if result_status == "PASS":
        st.write("If YOLO detects the expected class: MODEL TEST: PASS")
    elif result_status == "WRONG CLASS":
        st.write("If YOLO detects the wrong class: MODEL TEST: WRONG CLASS")
    else:
        st.write("If YOLO produces no detections: MODEL TEST: FAIL")

    st.markdown("---")
    st.write("This is a functional YOLO test only. It does not claim overall accuracy for the model.")


def render_batch_test() -> None:
    st.markdown("---")
    st.subheader("Optional Batch Test")
    uploaded_files = st.file_uploader(
        "Upload multiple images for batch testing",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Optional: test several images without adding them to the training dataset.",
    )

    if not uploaded_files:
        return

    expected_deposit = st.selectbox(
        "Expected class for batch testing",
        EXPECTED_OPTIONS,
        index=3,
        key="batch_expected_deposit",
    )

    if st.button("Run Batch YOLO Test"):
        expected_class = get_expected_class_value(expected_deposit)
        rows: list[dict[str, Any]] = []
        try:
            model = load_model(MODEL_PATH)
        except Exception as exc:
            st.error(f"Batch model loading error: {exc}")
            return

        for uploaded in uploaded_files:
            try:
                image = _load_image_from_upload(uploaded)
                raw = run_yolo_on_image(model, image, conf_threshold=0.0)
                accepted = [d for d in raw if d["confidence"] >= 0.25]

                if accepted:
                    top = accepted[0]
                    detected = top["class"]
                    confidence = f"{top['confidence'] * 100:.0f}%"
                    if expected_class in {"any_deposit", None}:
                        result = "PASS"
                    elif detected == expected_class:
                        result = "PASS"
                    else:
                        result = "WRONG CLASS"
                else:
                    detected = "none"
                    confidence = "-"
                    result = "FAIL"

                rows.append({
                    "Image": uploaded.name,
                    "Expected": expected_deposit,
                    "Predicted": detected,
                    "Confidence": confidence,
                    "Result": result,
                })
            except Exception:
                rows.append({
                    "Image": uploaded.name,
                    "Expected": expected_deposit,
                    "Predicted": "error",
                    "Confidence": "-",
                    "Result": "FAIL",
                })

        st.table(rows)


def main() -> None:
    render_single_image_test()
    render_batch_test()


if __name__ == "__main__":
    main()

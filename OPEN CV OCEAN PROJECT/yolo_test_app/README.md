# OceanAtlas - YOLO Model Tester

## 1. Purpose

This folder contains a temporary, isolated Streamlit application for testing the existing OceanAtlas YOLO model on uploaded images. It is used only for debugging and validation, not for training or production use.

The test app answers one question:

"Is the current YOLO model actually capable of detecting the underwater metal deposit image I am testing?"

## 2. Folder structure

```text
yolo_test_app/
├── app.py
├── README.md
├── requirements.txt
└── (temporary uploaded images are not saved permanently)
```

Everything in this folder is isolated from the production project. You can delete the entire folder when testing is complete.

## 3. Installation

From the project root, install the required packages into the existing virtual environment:

```powershell
cd "D:\DESKTOP\OPEN CV OCEAN PROJECT"
.\.venv\Scripts\python.exe -m pip install -r yolo_test_app\requirements.txt
```

## 4. How to start Streamlit

From the project root, run:

```powershell
streamlit run yolo_test_app/app.py
```

If you are using the project virtual environment, this is the exact command to run after activating the environment:

```powershell
cd "D:\DESKTOP\OPEN CV OCEAN PROJECT"
.\.venv\Scripts\Activate.ps1
streamlit run yolo_test_app/app.py
```

## 5. How to upload an image

1. Open the Streamlit page in the browser.
2. Click Upload Test Image.
3. Choose a JPG, JPEG, PNG, or WEBP image.
4. Select the expected deposit type.
5. Set the confidence threshold if needed.
6. Click Run YOLO Detection.

## 6. How to interpret results

The app does not claim accuracy from one image.

It shows:

- raw YOLO detections
- filtered detections after the confidence threshold
- detected class and confidence
- PASS / FAIL / WRONG CLASS based on the selected expected class

Examples:

- YOLO raw detection of polymetallic_nodules at 0.82 and expected class is Polymetallic Nodules -> PASS
- No detections returned by the model -> FAIL
- Detected cobalt_rich_crust while expected polymetallic_nodules -> WRONG CLASS

## 7. How to change MODEL_PATH

At the top of the Streamlit app there is a configuration variable:

```python
MODEL_PATH = "runs/detect/runs/detect-3/weights/best.pt"
```

If your current project model changes later, update that value in [yolo_test_app/app.py](yolo_test_app/app.py).

The app resolves the path relative to the project root and loads the actual YOLO checkpoint without copying it into the test folder.

## 8. How to delete the testing application after testing

When you are finished:

```powershell
Remove-Item -Recurse -Force "D:\DESKTOP\OPEN CV OCEAN PROJECT\yolo_test_app"
```

This removes the temporary testing application only. It does not touch the production OpenCV pipeline, training scripts, or YOLO project files outside the test folder.

## Notes

- This app uses the existing YOLO checkpoint only.
- It does not train, modify, or replace the production model.
- It does not modify the existing OpenCV live detector.
- It is only for debugging YOLO model behavior on uploaded images.

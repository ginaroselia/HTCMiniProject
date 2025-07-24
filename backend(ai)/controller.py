import requests
import time
import os
from PIL import Image
from io import BytesIO
from multiprocessing import Process, set_start_method
import tensorflow as tf
import base64
from keras.models import load_model
from ultralytics import YOLO
import numpy as np
import cv2
import json

# Load once globally
classification_model = load_model("models/ResNet/resnet.h5")
detection_model = YOLO('models/YOLO/yolo1.pt')  # You must have yolo1.pt locally
class_labels = ['Public Bank', 'Rototype', 'Standard Charted']

C_SHARP_API_BASE = "http://localhost:5231"  # your C# backend address


def limit_gpu_memory():
    """Make TensorFlow not consume 100% GPU memory."""
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print("✅ GPU memory growth enabled")
        except RuntimeError as e:
            print(f"❌ GPU error: {e}")


def fetch_next_job():
    try:
        res = requests.get(f"{C_SHARP_API_BASE}/ai/next_job", timeout=10, verify=False)
        res.raise_for_status()
        data = res.json()

        if not data or "image" not in data or "queueId" not in data:
            print("⚠️ Incomplete job data received.")
            return None

        image_data = base64.b64decode(data["image"])
        img = Image.open(BytesIO(image_data)).convert("RGB")

        return {
            "queueId": data["queueId"],
            "image": img
        }

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error: {http_err}")
        if http_err.response is not None:
            try:
                print("🔍 Response:", http_err.response.json())
            except Exception:
                print("🔍 Raw:", http_err.response.text)
        return None
    except Exception as e:
        print(f"❌ Fetch error: {e}")
        return None


def draw_detections(original_pil_img, results):
    img_cv = cv2.cvtColor(np.array(original_pil_img), cv2.COLOR_RGB2BGR)

    for box in results[0].boxes:
        cls_id = int(box.cls)
        label = detection_model.names[cls_id]
        score = float(box.conf)
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # Draw bounding box
        cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Label text
        text = f"{label} {score * 100:.1f}%"
        (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        text_x = max(x1, 5)
        text_y = max(y1 - 10, text_height + 5)

        cv2.rectangle(
            img_cv,
            (text_x, text_y - text_height - baseline),
            (text_x + text_width, text_y + baseline),
            (0, 255, 0),
            thickness=-1
        )
        cv2.putText(
            img_cv,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2
        )

    # Convert to base64
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    buffered = BytesIO()
    pil_img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def process_image(img):
    print("🧠 Running classification and detection...")

    # -------- CLASSIFICATION --------
    resized_img = img.resize((64, 32))
    img_array = np.array(resized_img)
    img_array = np.expand_dims(img_array, axis=0)
        
    prediction = classification_model.predict(img_array)[0]
    class_index = np.argmax(prediction)
    class_name = class_labels[class_index]
    confidence = float(prediction[class_index])

    # -------- DETECTION --------
    detection_results = detection_model.predict(img)
    detection_data = []
    for box in detection_results[0].boxes:
        label = detection_model.names[int(box.cls)]
        score = float(box.conf)
        bbox = box.xyxy[0].tolist()
        detection_data.append({
            'id': int(box.cls),
            'label': label,
            'confidence': round(score * 100, 2),
            'bbox': [round(coord, 2) for coord in bbox]
        })

    # -------- Annotated Image (base64) --------
    detected_img_base64 = draw_detections(img, detection_results)

    return {
        'prediction': class_name,
        'confidence': confidence,
        'objects': detection_data,
        'image': detected_img_base64
    }


def post_result(queue_id, result):
    payload = {
        "queueId": queue_id,
        "classification": {
            "prediction": result["prediction"],
            "confidence": round(result["confidence"] * 100, 2)
        },
        "detection": {
            "objects": result["objects"],
            "image": result["image"]
        }
    }
    try:
        res = requests.post(f"{C_SHARP_API_BASE}/ai/submit_result", json=payload, timeout=10, verify=False)
        res.raise_for_status()
        print(f"✅ Result posted for {queue_id}")
    except Exception as e:
        print(f"❌ Failed to post result: {e}")


def worker_loop(worker_id):
    print(f"🚀 Worker {worker_id} started")
    limit_gpu_memory()

    # 🔁 Load model here if needed (for real inference)
    # model = tf.keras.models.load_model("path/to/model")

    while True:
        job = fetch_next_job()
        if job:
            print(f"⏳ Worker {worker_id} processing...")
            result = process_image(job["image"])
            print(f"⏳ Worker {worker_id} returning result...")
            post_result(job["queueId"], result)
        else:
            print(f"⏳ Worker {worker_id} waiting...")
        time.sleep(3)


if __name__ == "__main__":
    try:
        set_start_method("spawn")  # Safer for TensorFlow (especially on Windows)
    except RuntimeError:
        pass  # already set

    workers = []
    num_workers = 4

    for i in range(num_workers):
        p = Process(target=worker_loop, args=(i,))
        p.start()
        workers.append(p)

    for p in workers:
        p.join()

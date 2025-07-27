import requests # For making HTTP requests to the C# backend
import time # For adding delays between tasks
import os # For file and system-related tasks
from PIL import Image # For working with images
from io import BytesIO # For reading/writing 
from multiprocessing import Process, set_start_method # For running multipleworkers
import tensorflow as tf # For running classification
import base64 # For encoding/decoding images as text
from keras.models import load_model # For loading saved ML models
from ultralytics import YOLO # For using YOLO object detection model
import numpy as np # For handling imgage arrays
import cv2 # OpenCV for drawing and processing images
import json # For working with JSON data

from rfdetr import RFDETRBase # For using DETR object detection model
from dotenv import load_dotenv

# Load environment variables for API keys
# load_dotenv()

# Store keys in variables (if needed later)
# hugging_face_key = os.getenv("HUGGING_FACE_API")
# roboflow_key = os.getenv("ROBOFLOW_API")

# Load the classification and detection models once globally
classification_model = load_model("models/ResNet/resnet.h5")
# classification_model = load_model("models/ResNet/resnet3000v2220720251237goodoverall.h5")


# YOLO
# detection_model = YOLO('models/YOLO/yolo5.pt') 

# DETR
detection_model = RFDETRBase(pretrain_weights="models/DETR/detr.pth")

# Labels for classification results
class_labels = ['Public Bank', 'Rototype', 'Standard Charted'] 

# URL of the backend API (C# server)
C_SHARP_API_BASE = "http://localhost:5231"  


def limit_gpu_memory():
    """Make TensorFlow not consume 100% GPU memory."""
    gpus = tf.config.list_physical_devices('GPU') # Get available GPUs
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True) # Let GPU memory grow as needed
            print("✅ GPU memory growth enabled")
        except RuntimeError as e:
            print(f"❌ GPU error: {e}")


def fetch_next_job():
    """Ask the C# backend for the next image to process"""
    try:
        # Send GET request to get the next job (image + queueId)
        res = requests.get(f"{C_SHARP_API_BASE}/ai/next_job", timeout=10, verify=False)
        res.raise_for_status()
        data = res.json()

        # Check if response contains required data
        if not data or "image" not in data or "queueId" not in data:
            print("⚠️ Incomplete job data received.")
            return None
        
        # Convert the base64 image into a PIL image
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

# YOLO

# def draw_detections(original_pil_img, results):
#     """Draw boxes and labels on image using detection results"""

#     # Convert PIL image to OpenCV (BGR)
#     img_cv = cv2.cvtColor(np.array(original_pil_img), cv2.COLOR_RGB2BGR)

#     for box in results[0].boxes:
#         cls_id = int(box.cls) # Class index
#         label = detection_model.names[cls_id] # Get label name
#         score = float(box.conf) # Confidence score
#         x1, y1, x2, y2 = map(int, box.xyxy[0].tolist()) # Box coordinated

#         # Draw bounding box
#         cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 2)

#         # Prepare label text
#         text = f"{label} {score * 100:.1f}%"
#         (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
#         text_x = max(x1, 5)
#         text_y = max(y1 - 10, text_height + 5)

#         # Draw label background
#         cv2.rectangle(
#             img_cv,
#             (text_x, text_y - text_height - baseline),
#             (text_x + text_width, text_y + baseline),
#             (0, 255, 0),
#             thickness=-1
#         )

#         # Draw label text
#         cv2.putText(
#             img_cv,
#             text,
#             (text_x, text_y),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.6,
#             (0, 0, 0),
#             2
#         )

#     # Convert back to RGB and encode to base64
#     img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
#     pil_img = Image.fromarray(img_rgb)
#     buffered = BytesIO()
#     pil_img.save(buffered, format="JPEG")
#     return base64.b64encode(buffered.getvalue()).decode("utf-8")


# DETR
def draw_detections(original_pil_img, detections):
    img_cv = cv2.cvtColor(np.array(original_pil_img), cv2.COLOR_RGB2BGR)

    for det in detections:
        label = det['label']
        score = det['confidence']
        x1, y1, x2, y2 = map(int, det['bbox'])

        # Draw bounding box
        cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw label and score
        text = f"{label} {score:.1f}%"
        (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

        text_x = x2 + 5
        text_y = y1 + text_height if y1 + text_height + 5 < img_cv.shape[0] else y1 - 5
        if text_x + text_width > img_cv.shape[1]:
            text_x = x1 - text_width - 5

        cv2.rectangle(
            img_cv,
            (text_x, text_y - text_height - baseline),
            (text_x + text_width, text_y + baseline),
            (0, 255, 0),
            thickness=-1
        )
        cv2.putText(img_cv, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # Convert to base64
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    buffered = BytesIO()
    pil_img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")



def process_image(img):
    """Run classification and detection on the image"""
    print("🧠 Running classification and detection...")

    # -------- CLASSIFICATION --------
    resized_img = img.resize((64, 32)) # Resize image for model
    img_array = np.array(resized_img)
    img_array = np.expand_dims(img_array, axis=0) # Add batch dimension
        
    prediction = classification_model.predict(img_array)[0] # Get prediction scores
    class_index = np.argmax(prediction) # Highest score index
    class_name = class_labels[class_index] # Convert to label
    confidence = float(prediction[class_index]) # Get score

    # -------- DETECTION (YOLO) --------

    # detection_results = detection_model.predict(img)
    # detection_data = []
    # for box in detection_results[0].boxes:
    #     label = detection_model.names[int(box.cls)]
    #     score = float(box.conf)
    #     bbox = box.xyxy[0].tolist()
    #     detection_data.append({
    #         'id': int(box.cls),
    #         'label': label,
    #         'confidence': round(score * 100, 2),
    #         'bbox': [round(coord, 2) for coord in bbox]
    #     })
    
    # -------- Annotated Image (base64) --------
    # detected_img_base64 = draw_detections(img, detection_results)



    # -------- DETECTION (Roboflow DETR) --------
    rf_results = detection_model.predict(img, threshold=0.5)

    detection_class_names = ['Test', 'Logo', 'Payee'] 

    detection_data = []
    for i in range(len(rf_results.xyxy)):
        bbox = rf_results.xyxy[i]
        score = rf_results.confidence[i]
        class_id = int(rf_results.class_id[i])
        label = detection_class_names[class_id]

        detection_data.append({
            'id': class_id,
            'label': label,
            'confidence': round(float(score) * 100, 2),
            'bbox': [round(float(coord), 2) for coord in bbox]
        })
        
    # # -------- Annotated Image (base64) --------
    detected_img_base64 = draw_detections(img, detection_data)

    return {
    'prediction': class_name,
    'confidence': confidence,
    'objects': detection_data,
    'image': detected_img_base64
    }



def post_result(queue_id, result):
    """Send the processed result back to the C# server"""
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
        # Send result to /submit_result endpoint
        res = requests.post(f"{C_SHARP_API_BASE}/ai/submit_result", json=payload, timeout=10, verify=False)
        res.raise_for_status()
        print(f"✅ Result posted for {queue_id}")
    except Exception as e:
        print(f"❌ Failed to post result: {e}")


def worker_loop(worker_id):
    """This function runs inside a worker process"""
    print(f"🚀 Worker {worker_id} started")
    limit_gpu_memory()

    while True:
        job = fetch_next_job() # Ask server for new job
        if job:
            print(f"⏳ Worker {worker_id} processing...")
            result = process_image(job["image"]) # Analyze the image
            print(f"⏳ Worker {worker_id} returning result...")
            post_result(job["queueId"], result) # Send back result
        else:
            print(f"⏳ Worker {worker_id} waiting...")  # No job, sleep and try later
        time.sleep(3) # Wait 3 seconds before asking again


if __name__ == "__main__":
    try:
        set_start_method("spawn") # Required for TensorFlow multiprocessing (especially on Windows)
    except RuntimeError:
        pass  # Method already set

    workers = []
    num_workers = 4 # Number of parallel processes

    # Create and start worker processes
    for i in range(num_workers):
        p = Process(target=worker_loop, args=(i,))
        p.start()
        workers.append(p)

    # Wait for all workers to finish
    for p in workers:
        p.join()

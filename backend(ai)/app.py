from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from keras.models import load_model
import numpy as np
from PIL import Image

from ultralytics import YOLO
from rfdetr import RFDETRBase

import io
import base64
import cv2


# Load environment variables for API keys (For Roboflow)
load_dotenv()

# Store keys in variables to be used in loading Roboflow DETR model
hugging_face_key = os.getenv("HUGGING_FACE_API")
roboflow_key = os.getenv("ROBOFLOW_API")

# For initializing and configuring flask app itself
app = Flask(__name__)
CORS(app)

# Load models
classification_model = load_model('resnet.h5')
# classification_model = load_model('model13.keras')
detection_model = YOLO('yolo1.pt')

"""Load Roboflow"""
roboflow_detection_model = RFDETRBase(pretrain_weights="roboflow-detr_checkpoint_best_total.pth")

# Class labels for classification model
class_labels = ['Public Bank', 'Rototype', 'Standard Charted']


def draw_detections(original_pil_img, results):
    img_cv = cv2.cvtColor(np.array(original_pil_img), cv2.COLOR_RGB2BGR)

    for box in results[0].boxes:
        cls_id = int(box.cls)
        label = detection_model.names[cls_id]
        score = float(box.conf)
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # Draw bounding box
        cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Label text beside box
        text = f"{label} {score * 100:.1f}%"
        (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

        # Position label beside box (to the right)
        text_x = x2 + 5
        text_y = y1 + text_height if y1 + text_height + 5 < img_cv.shape[0] else y1 - 5

        # Adjust if it goes off image width
        if text_x + text_width > img_cv.shape[1]:
            text_x = x1 - text_width - 5

        # Background rectangle
        cv2.rectangle(
            img_cv,
            (text_x, text_y - text_height - baseline),
            (text_x + text_width, text_y + baseline),
            (0, 255, 0),
            thickness=-1
        )

        # Draw text
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
    buffered = io.BytesIO()
    pil_img.save(buffered, format="JPEG")
    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_image





@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    original_img = Image.open(file.stream).convert('RGB')

    # -------- CLASSIFICATION --------
    resized_img = original_img.resize((64, 32))
    # resized_img = original_img.resize((227, 227))
    img_array = np.array(resized_img)
    img_array = np.expand_dims(img_array, axis=0)
    prediction = classification_model.predict(img_array)[0]
    class_index = np.argmax(prediction)
    class_name = class_labels[class_index]
    confidence = float(prediction[class_index])

    # -------- DETECTION --------
    """YOLO"""
    detection_results = detection_model.predict(original_img)
    detection_data = []
    for box in detection_results[0].boxes:
        label = detection_model.names[int(box.cls)]
        score = float(box.conf)
        bbox = box.xyxy[0].tolist()
        detection_data.append({
            'label': label,
            'confidence': round(score * 100, 2),
            'bbox': [round(coord, 2) for coord in bbox]
        })

    """ROBOFLOW"""
    # The predict for roboflow needs to put a threshold parameter value
    test_prediction = detection_model.predict(test_image, threshold=0.5)


    # Get annotated image
    detected_img_base64 = draw_detections(original_img, detection_results)

    return jsonify({
        'classification': {
            'prediction': class_name,
            'confidence': round(confidence * 100, 2)
        },
        'detection': {
            'objects': detection_data,
            'image': detected_img_base64
        }
    })


if __name__ == '__main__':
    app.run(port=5000)

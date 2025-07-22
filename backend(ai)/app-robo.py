from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from keras.models import load_model
import numpy as np
from PIL import Image

from rfdetr import RFDETRBase  # Roboflow DETR

import io
import base64
import cv2

# Load environment variables for API keys
load_dotenv()

# Store keys in variables (if needed later)
hugging_face_key = os.getenv("HUGGING_FACE_API")
roboflow_key = os.getenv("ROBOFLOW_API")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load models
classification_model = load_model('resnet.h5')
roboflow_detection_model = RFDETRBase(pretrain_weights="detr.pth")

# Class labels for classification model
class_labels = ['Public Bank', 'Rototype', 'Standard Charted']

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
    img_array = np.array(resized_img)
    img_array = np.expand_dims(img_array, axis=0)
    prediction = classification_model.predict(img_array)[0]
    class_index = np.argmax(prediction)
    class_name = class_labels[class_index]
    confidence = float(prediction[class_index])

    # -------- DETECTION (Roboflow DETR) --------
    rf_results = roboflow_detection_model.predict(original_img, threshold=0.5)
    
    detection_class_names = ['Test','Logo', 'Payee']

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

    print("Number of detections:", len(rf_results.xyxy))
    print("All class_ids:", rf_results.class_id)

  
    # Get annotated image
    detected_img_base64 = draw_detections(original_img, detection_data)

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

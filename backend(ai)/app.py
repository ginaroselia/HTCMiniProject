from flask import Flask, request, jsonify
from flask_cors import CORS
from keras.models import load_model
import numpy as np
from PIL import Image
from ultralytics import YOLO
import io
import base64
import cv2

app = Flask(__name__)
CORS(app)

# Load models
classification_model = load_model('resnet.h5')
# classification_model = load_model('model13.keras')
detection_model = YOLO('yolo1.pt')


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
    img = Image.open(file.stream).convert('RGB')
    # img = img.resize((227, 227)) 
    img = img.resize((64, 32))
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)

    print("Input array shape:", img_array.shape, flush=True)
    print("Input min/max:", img_array.min(), img_array.max(), flush=True)

    prediction = model.predict(img_array)[0]
    
    print("Prediction vector:", prediction, flush=True)
    class_index = np.argmax(prediction)
    class_name = class_labels[class_index]
    confidence = float(prediction[class_index])
    

    return jsonify({
        'prediction': class_name,
        'confidence': round(confidence * 100, 2)
    })

if __name__ == '__main__':
    app.run(port=5000)

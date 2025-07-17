from flask import Flask, request, jsonify
from flask_cors import CORS
from keras.models import load_model
import numpy as np
from PIL import Image

app = Flask(__name__)
CORS(app)  # Allow React frontend to access backend

model = load_model('resnet.h5')  # Ensure this file is in same folder
print("✅ Model loaded successfully!")

class_labels = ['Public Bank', 'Rototype', 'Standard Charted']  # Change to your model's actual labels

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    img = Image.open(file.stream).convert('RGB')
    # img = img.resize((227, 227)) 
    img = img.resize((64, 32)) 
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

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

from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import os

# Load the model
model_path = "resnet.h5"
model = load_model(model_path)
print(f"✅ Model loaded from: {os.path.abspath(model_path)}")

# Define your class labels first
class_labels = ['Public Bank', 'Rototype', 'Standard Charted']

# Loop through test images
for img_file in ["pb.png", "roto.png", "sc.png"]:
    # img = Image.open(img_file).convert("RGB").resize((227, 227))
    img = Image.open(img_file).convert("RGB").resize((64, 32)) # resnet size
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    
    prediction = model.predict(img_array)
    predicted_class = class_labels[np.argmax(prediction)]
    
    print(f"{img_file}: {predicted_class} → {prediction}")

import os
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np

def download_movenet():
    # Create models directory if it doesn't exist
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(model_dir, exist_ok=True)

    print("Downloading MoveNet model from TensorFlow Hub...")
    model = hub.load('https://tfhub.dev/google/movenet/singlepose/lightning/4')
    
    # Get the concrete function
    concrete_func = model.signatures['serving_default']
    frozen_func = tf.function(lambda x: concrete_func(x))
    frozen_func = frozen_func.get_concrete_function(
        tf.TensorSpec(shape=[1, 192, 192, 3], dtype=tf.int32))
    
    # Convert to TFLite
    converter = tf.lite.TFLiteConverter.from_concrete_functions([frozen_func])
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS
    ]
    tflite_model = converter.convert()
    
    # Save the model
    model_path = os.path.join(model_dir, 'movenet_lightning.tflite')
    with open(model_path, 'wb') as f:
        f.write(tflite_model)
    
    print(f"Model saved to {model_path}")

if __name__ == '__main__':
    download_movenet()
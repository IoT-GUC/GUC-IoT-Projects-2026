import tensorflow as tf
import numpy as np
from pathlib import Path
import json

# ── CONFIGURE ────────────────────────────────────────────────
MODEL_PATH   = r"FOMO+CNN\digit_cnn\best_model.keras"
DATASET_ROOT = r"dataset\final\cnn_dataset"
OUTPUT_DIR   = r"FOMO+CNN\digit_cnn"
IMG_SIZE     = (28, 28)
# ─────────────────────────────────────────────────────────────

model = tf.keras.models.load_model(MODEL_PATH)

# ── Build representative dataset for INT8 calibration ────────
def representative_dataset():
    ds = tf.keras.utils.image_dataset_from_directory(
        Path(DATASET_ROOT) / "valid",
        image_size=IMG_SIZE,
        batch_size=1,
        color_mode="grayscale",
        label_mode=None,
        shuffle=True,
        seed=42,
    )
    for img in ds.take(200):
        yield [tf.cast(img, tf.float32)]

# ── Convert to INT8 TFLite ────────────────────────────────────
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type  = tf.uint8
converter.inference_output_type = tf.uint8

tflite_model = converter.convert()

# ── Save ──────────────────────────────────────────────────────
out_path = Path(OUTPUT_DIR) / "digit_cnn_int8.tflite"
out_path.write_bytes(tflite_model)

size_kb = len(tflite_model) / 1024
print(f"Model saved: {out_path}")
print(f"Model size: {size_kb:.1f} KB")

# ── Quick sanity check ────────────────────────────────────────
interpreter = tf.lite.Interpreter(model_path=str(out_path))
interpreter.allocate_tensors()

inp  = interpreter.get_input_details()
out  = interpreter.get_output_details()
print(f"\nInput:  shape={inp[0]['shape']}  dtype={inp[0]['dtype']}")
print(f"Output: shape={out[0]['shape']}  dtype={out[0]['dtype']}")
print("\nExport successful.")
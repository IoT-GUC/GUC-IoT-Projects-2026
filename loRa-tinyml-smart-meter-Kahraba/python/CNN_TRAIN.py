import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pathlib import Path
from sklearn.utils.class_weight import compute_class_weight
import json

# ── CONFIGURE ────────────────────────────────────────────────
DATASET_ROOT = r"dataset\final\cnn_dataset"
OUTPUT_DIR   = r"FOMO+CNN\digit_cnn"
IMG_SIZE     = (28, 28)
BATCH_SIZE   = 32
EPOCHS       = 60
CLASS_NAMES  = ["0","1","2","3","4","5","6","7","8","9","dot"]
# ─────────────────────────────────────────────────────────────

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ── Load datasets (NO normalization here) ────────────────────
train_ds = keras.utils.image_dataset_from_directory(
    Path(DATASET_ROOT) / "train",
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    color_mode="grayscale",
    class_names=CLASS_NAMES,
    label_mode="int",
    shuffle=True,
    seed=42,
)

valid_ds = keras.utils.image_dataset_from_directory(
    Path(DATASET_ROOT) / "valid",
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    color_mode="grayscale",
    class_names=CLASS_NAMES,
    label_mode="int",
    shuffle=False,
)

# ── Compute class weights ─────────────────────────────────────
all_labels = np.concatenate([y.numpy() for _, y in train_ds])
class_weights = compute_class_weight("balanced",
                                      classes=np.arange(11),
                                      y=all_labels)
class_weight_dict = dict(enumerate(class_weights))
print("\nClass weights:")
for i, name in enumerate(CLASS_NAMES):
    print(f"  {name}: {class_weight_dict[i]:.3f}")

# ── Augmentation (training only, applied via dataset map) ─────
def augment(image, label):
    image = tf.cast(image, tf.float32)
    image = tf.image.random_brightness(image, 0.2)
    image = tf.image.random_contrast(image, 0.8, 1.2)
    image = tf.clip_by_value(image, 0.0, 255.0)
    return image, label

train_ds = train_ds.map(augment, num_parallel_calls=tf.data.AUTOTUNE)

# ── Prefetch ──────────────────────────────────────────────────
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().prefetch(AUTOTUNE)
valid_ds = valid_ds.cache().prefetch(AUTOTUNE)

# ── Model (normalization INSIDE model — can never be skipped) ──
model = keras.Sequential([
    keras.Input(shape=(28, 28, 1)),

    # normalization baked in — divides by 255 always
    layers.Rescaling(1.0 / 255.0),

    layers.Conv2D(16, 3, padding="same", activation="relu"),
    layers.BatchNormalization(),
    layers.MaxPooling2D(),                          # → 14x14

    layers.Conv2D(32, 3, padding="same", activation="relu"),
    layers.BatchNormalization(),
    layers.MaxPooling2D(),                          # → 7x7

    layers.Conv2D(64, 3, padding="same", activation="relu"),
    layers.BatchNormalization(),
    layers.GlobalAveragePooling2D(),                # → 64

    layers.Dropout(0.3),
    layers.Dense(64, activation="relu"),
    layers.Dense(11, activation="softmax"),
], name="digit_cnn")

model.summary()

# ── Compile ───────────────────────────────────────────────────
model.compile(
    optimizer=keras.optimizers.Adam(1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

# ── Callbacks ─────────────────────────────────────────────────
callbacks = [
    keras.callbacks.ModelCheckpoint(
        filepath=str(Path(OUTPUT_DIR) / "best_model.keras"),
        monitor="val_accuracy",
        save_best_only=True,
        verbose=1,
    ),
    keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=10,
        restore_best_weights=True,
        verbose=1,
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=5,
        verbose=1,
    ),
]

# ── Train ─────────────────────────────────────────────────────
history = model.fit(
    train_ds,
    validation_data=valid_ds,
    epochs=EPOCHS,
    class_weight=class_weight_dict,
    callbacks=callbacks,
)

# ── Save class names ──────────────────────────────────────────
with open(Path(OUTPUT_DIR) / "class_names.json", "w") as f:
    json.dump(CLASS_NAMES, f)

print(f"\nBest model saved to {OUTPUT_DIR}/best_model.keras")
print(f"Final val_accuracy: {max(history.history['val_accuracy']):.4f}")
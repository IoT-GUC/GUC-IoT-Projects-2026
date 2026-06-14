

# Smart Meter Reader — ESP32-CAM + FOMO + YOLO + UART/LoRa

## 1. Project overview

This project implements an embedded IoT meter-reading prototype.

The system captures an electricity/gas/water meter display using an **ESP32-CAM**, detects the LCD/display area using a lightweight **Edge Impulse FOMO model**, crops the display region, runs a lightweight **YOLO digit detector** on the cropped image, constructs the final reading, and sends the result over **UART** to a **LilyGO board** for display and/or LoRa forwarding.

The final working pipeline is:

```text
ESP32-CAM capture
    ↓
Burst capture
    ↓
FOMO screen detection
    ↓
Dynamic LCD crop
    ↓
YOLO digit detection on cropped display
    ↓
Letterbox preprocessing
    ↓
Confidence filtering + row filtering
    ↓
Sort detections left-to-right
    ↓
Final reading string
    ↓
UART to LilyGO
    ↓
Display / LoRa forwarding
```

Current final status:

```text
ESP32-CAM capture ✅
burst capture ✅
FOMO dynamic crop ✅
YOLO inference on ESP32 ✅
letterbox preprocessing ✅
row filtering ✅
UART PROCESSING + final result ✅
LilyGO display/forwarding ready ✅
```

### 1.1 Final ESP32-CAM sketch used

The final ESP32-CAM firmware file is:

```text
esp32cam_chirale_fomo_yolo_uart_v4_burst.ino
```

This sketch runs the complete embedded pipeline:

```text
Capture burst frames → decode JPEG to RGB → run FOMO → crop LCD → letterbox to 160×160 → run YOLO → decode output → NMS → row filtering → construct reading → choose best burst result → send UART packet
```

Main files required in the same Arduino sketch folder:

```text
esp32cam_chirale_fomo_yolo_uart_v4_burst.ino
digit_model_data_full_integer.h
fomo_model_data.h
```

The sketch sends UART packets in this format:

```text
METER|READING=<reading>|CONF=<confidence>|STATUS=<status>
```

Example boot packet:

```text
METER|READING=BOOT|CONF=1.00|STATUS=READY
```

Example processing packet:

```text
METER|READING=....|CONF=0.00|STATUS=PROCESSING
```

---



## 2. Hardware used

### 2.1 Main hardware

| Component | Purpose |
|---|---|
| ESP32-CAM AI-Thinker | Captures meter image and runs the embedded inference pipeline |
| OV2640 camera module | Camera used by ESP32-CAM |
| microSD card | Required by the current implementation for image/debug storage |
| FTDI USB-to-Serial adapter | Used to upload sketches to the ESP32-CAM |
| LilyGO board | Receives final reading from ESP32-CAM over UART and displays/forwards it |
| LoRa module / LilyGO LoRa board | Used or prepared for wireless forwarding |
| Breadboard + jumper wires | Wiring between FTDI, ESP32-CAM, and LilyGO |
| Pushbuttons 1 | used for enabling and disabling the LED and the other is for capturing |
| Stable 5V supply | Required because ESP32-CAM can be unstable with weak power |

### 2.2 Important note about SD card

The current ESP32-CAM implementation expects a **microSD card to be inserted**.

The SD card is used for one or more of the following depending on the sketch version:

- saving raw captures
- saving LCD crops
- debugging model behavior
- storing intermediate test images/logs

Before running the final ESP32-CAM sketch, insert a formatted microSD card.

Recommended format:

```text
FAT32
```

---

## 3. Software and libraries

### 3.1 Arduino / embedded software

Install the following:

1. **Arduino IDE** or **PlatformIO**
2. ESP32 board package
3. ESP32-CAM AI-Thinker board support
4. LilyGO board support matching the used LilyGO board LilyGO T-display
5. **Chirale_TensorFlowLite** Arduino library
6. TensorFlow Lite Micro headers included through Chirale_TensorFlowLite
7. ESP32 camera/SD libraries included with the ESP32 board package
8. Any display/LoRa libraries required by the LilyGO sketch

### 3.2 Boards

For ESP32-CAM upload, select:

```text
Board: AI Thinker ESP32-CAM
```

Typical Arduino settings:

```text
Board: AI Thinker ESP32-CAM
Upload Speed: 115200 or 921600
CPU Frequency: 240 MHz
Flash Frequency: 40 MHz
Flash Mode: QIO or DIO depending board stability
Partition Scheme: Huge APP or a scheme that fits the sketch/model
PSRAM: Enabled
```

For LilyGO, select the board matching the actual module used.

Common examples:

```text

LILYGO T-Display

```

Use the exact board matching the uploaded LilyGO sketch and hardware.

### 3.3 Final TensorFlow Lite library used

The final ESP32-CAM sketch uses:

```cpp
#include <Chirale_TensorFlowLite.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
```

So the required Arduino inference library is:

```text
Chirale_TensorFlowLite
```

Important implementation note: the final sketch intentionally runs **both** the FOMO model and the YOLO model using `Chirale_TensorFlowLite`. It does **not** include the normal Edge Impulse generated `smart-meter-screen-fomo_inferencing` library in the final sketch, because including both Edge Impulse TFLM and another TensorFlow Lite Micro library may cause duplicate TensorFlow Lite Micro symbols.

The final model headers expected in the same sketch folder are:

```text
digit_model_data_full_integer.h
fomo_model_data.h
```

These files contain the converted `.tflite` models as C arrays.

---

## 4. ESP32-CAM upload instructions

The ESP32-CAM does not have a built-in USB port, so upload is done using an FTDI USB-to-Serial adapter.

### 4.1 FTDI to ESP32-CAM wiring for upload

Connect:

| FTDI | ESP32-CAM |
|---|---|
| 5V | 5V |
| GND | GND |
| TX | U0R / RX |
| RX | U0T / TX |
| GND | GPIO0 |

Important:

```text
FTDI TX connects to ESP32-CAM RX
FTDI RX connects to ESP32-CAM TX
GPIO0 must be connected to GND only during upload
```

### 4.2 Upload steps

1. Connect FTDI to ESP32-CAM with TX/RX crossed.
2. Connect `GPIO0` to `GND`.
3. Plug the FTDI into the laptop.
4. Open Arduino IDE.
5. Select board: `AI Thinker ESP32-CAM`.
6. Select the correct COM port.
7. Click Upload.
8. When upload finishes, disconnect `GPIO0` from `GND`.
9. Press the ESP32-CAM reset button, or unplug and plug the board again.
10. Open Serial Monitor at the baud rate used in the sketch.

If upload gets stuck at:

```text
Connecting........
```

press the ESP32-CAM reset button once while uploading.

### 4.3 Running after upload

For normal run mode:

```text
GPIO0 must NOT be connected to GND.
```

Then reset or power-cycle the ESP32-CAM.

---

## 5. Breadboard / wiring connections

### 5.1 ESP32-CAM + FTDI upload wiring

```text
FTDI 5V  → ESP32-CAM 5V
FTDI GND → ESP32-CAM GND
FTDI TX  → ESP32-CAM U0R / RX
FTDI RX  → ESP32-CAM U0T / TX
ESP32-CAM GPIO0 → GND only during upload
```

Remove `GPIO0 → GND` after upload.

### 5.2 ESP32-CAM to LilyGO UART wiring

For sending final readings from ESP32-CAM to LilyGO:

```text
ESP32-CAM TX → LilyGO RX
ESP32-CAM GND → LilyGO GND
```

If two-way UART is needed:

```text
ESP32-CAM RX ← LilyGO TX
```

Make sure both boards share a common ground.

### 5.3 Power notes

ESP32-CAM is sensitive to unstable power. Use a stable 5V supply.  
If the camera freezes, resets, or gives corrupted images, check:

- weak USB cable
- weak FTDI 5V output
- unstable breadboard connections
- missing common ground
- insufficient current supply

---

## 6. FOMO screen detector training on Edge Impulse

### 6.1 Purpose of the FOMO model

The FOMO model is used to detect the screen/LCD region in the full ESP32-CAM image.

It does **not** read the digits directly.  
It only helps the firmware know where to crop.

Final usage:

```text
ESP32-CAM full image
    ↓
FOMO detects screen location
    ↓
Firmware creates LCD crop
    ↓
YOLO reads digits from crop
```

### 6.2 Why FOMO was selected

FOMO was selected because it is lightweight and suitable for embedded devices.

YOLO for both screen detection and digit detection was too heavy for the ESP32-CAM.  
So the project uses a hybrid architecture:

```text
FOMO → screen localization
YOLO → digit detection after cropping
```

### 6.3 Edge Impulse training steps

1. Open Edge Impulse.
2. Create a new project.
3. Upload screen/meter images.
4. Label the LCD/screen region as one object class, for example:

```text
screen
```

5. Go to **Impulse Design**.
6. Create an image impulse.
7. Choose image input size supported by the project.
8. Add an image processing block.
9. Add **Object Detection (FOMO)** as the learning block.
10. Train the model.
11. Check model performance.
12. Test with real ESP32-CAM images.
13. Deploy as an **Arduino library** in our case we deployed as a cpp library and the refrence engine to be TFlite and took the cpp file from the zip to be the .h file in the sketch folder.

### 6.4 Exporting/deploying FOMO to Arduino

In Edge Impulse:

```text
Deployment → Arduino library → Build
```

Download the generated `.zip`.

In Arduino IDE:

```text
Sketch → Include Library → Add .ZIP Library
we tried this at first but only fomo worked alone so for both yolo and fomo to work we need 1 TF library and 2 .h files 
```

Then include the generated library in the ESP32-CAM final sketch.

The include usually looks like:

```cpp
#include <your_edge_impulse_project_name_inferencing.h>
```

Example structure in the final sketch:

```cpp
#include <esp_camera.h>
#include <SD_MMC.h>
#include <your_fomo_model_inferencing.h>
```

The exact include name depends on the Edge Impulse project/library name.

### 6.5 How FOMO was added to the final sketch

The FOMO model is added as an exported Edge Impulse Arduino library.

The final ESP32-CAM sketch:

1. Captures an image from the camera.
2. Converts/prepares the image for Edge Impulse input.
3. Calls the Edge Impulse classifier/inference function.
4. Reads the FOMO detection result.
5. Uses the detected screen position to compute the crop rectangle.
6. Crops the image before YOLO digit detection.

Conceptual pseudocode:

```cpp
camera_fb_t *fb = esp_camera_fb_get();

run_fomo_inference(fb);

if (screen_detected) {
    crop_x = detected_x - margin_x;
    crop_y = detected_y - margin_y;
    crop_w = detected_w + margins;
    crop_h = detected_h + margins;
}
```

---

## 7. Adjusting FOMO dynamic crop or fixed crop

The final sketch may support either:

1. FOMO-based dynamic crop
2. fixed/manual crop fallback

### 7.1 FOMO dynamic crop

Look in the ESP32-CAM final sketch for variables similar to:

```cpp
CROP_PAD_X
CROP_PAD_Y
LCD_CROP_W
LCD_CROP_H
FOMO_MARGIN_X
FOMO_MARGIN_Y
```

or logic similar to:

```cpp
cropX = fomoX - padX;
cropY = fomoY - padY;
cropW = fomoW + 2 * padX;
cropH = fomoH + 2 * padY;
```

To make the crop wider:

```cpp
padX += value;
```

To make the crop taller:

```cpp
padY += value;
```

To shift crop right:

```cpp
cropX += value;
```

To shift crop left:

```cpp
cropX -= value;
```

To shift crop down:

```cpp
cropY += value;
```

To shift crop up:

```cpp
cropY -= value;
```

### 7.2 Fixed crop fallback

If the sketch uses fixed crop values, look for constants similar to:

```cpp
#define FIXED_CROP_X
#define FIXED_CROP_Y
#define FIXED_CROP_W
#define FIXED_CROP_H
```

or:

```cpp
int cropX = ...;
int cropY = ...;
int cropW = ...;
int cropH = ...;
```

Change these values carefully, then re-upload the sketch.

Recommended tuning method:

1. Save debug crops to SD card.
2. Open the saved crops on laptop.
3. Check whether the full LCD digits are visible.
4. Adjust crop values.
5. Re-upload or rerun.
6. Repeat until the crop is centered.

---

## 8. Python FOMO crop/segmentation test

Before full embedded integration, the FOMO crop behavior was tested in Python.

Purpose of the Python test:

```text
Verify that the FOMO screen detection can be converted into a usable LCD crop.
```

Typical Python test flow:

```text
Load image
    ↓
Run/parse FOMO-like screen detection output
    ↓
Compute crop rectangle
    ↓
Crop LCD region
    ↓
Save/debug crop
```

Expected folder:

```text
python/fomo_crop.py/
```

Recommended files:

```text
fomo_segmentation_test.py
README.md
sample_inputs/
sample_outputs/
```

This test is useful because it allows crop tuning quickly before changing the embedded C++ sketch.

---

## 9. YOLO digit detector training on Kaggle

### 9.1 Why Kaggle was used

YOLO training on images can take a long time locally, especially without a GPU.

Kaggle provides free GPU sessions, so the YOLO digit detector was trained there.

Use Kaggle for:

```text
dataset loading
YOLO training
validation
TFLite export
visual prediction tests
```

### 9.2 Notebook used

The main training notebook is:

```text
python/yolo_training/yolo-digit-detector.ipynb
```

The uploaded notebook installs and uses:

```text
ultralytics==8.3.40
numpy==1.26.4
opencv-python-headless==4.10.0.84
```

It also uses:

```text
torch
torchvision
cv2
matplotlib
pandas
scipy
seaborn
Pillow
```

### 9.3 Dataset format

The dataset uses YOLO format:

```text
dataset/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

Classes:

```text
0: 0
1: 1
2: 2
3: 3
4: 4
5: 5
6: 6
7: 7
8: 8
9: 9
10: dot
```

The notebook generates a Kaggle YAML file:

```yaml
path: /kaggle/input/datasets/kareemriad025/merged-digit-dataset/merged_digit_dataset

train: train/images
val: val/images
test: test/images

nc: 11

names:
  0: "0"
  1: "1"
  2: "2"
  3: "3"
  4: "4"
  5: "5"
  6: "6"
  7: "7"
  8: "8"
  9: "9"
  10: "dot"
```

If the dataset path changes, update:

```python
DATASET_ROOT = Path("/kaggle/input/...")
```

and regenerate the YAML.

---

## 10. YOLO training path used

### 10.1 First model: YOLOv8n at 320×320

The first model was trained using:

```python
model = YOLO("yolov8n.pt")

model.train(
    data=DATA_YAML,
    epochs=100,
    imgsz=320,
    batch=16,
    patience=25,
    device=0,
    workers=2,
    project="/kaggle/working/runs_digit_detector",
    name="yolov8n_digits_320",
    pretrained=True,
    optimizer="AdamW",
    lr0=0.001,
    cos_lr=True,
    mosaic=0.3,
    close_mosaic=20,
    plots=True
)
```

Purpose:

```text
Validate the dataset and get a stronger teacher/reference model.
```

Why it was not final:

```text
The 320 model was too heavy for ESP32-CAM deployment.
```

### 10.2 Custom micro YOLO architecture

A smaller YOLO-like architecture was created manually in the notebook.

Purpose:

```text
Reduce model size and memory usage so that inference can run on ESP32-CAM.
```

The model has smaller channels such as:

```text
8, 16, 32, 48
```

instead of the full YOLOv8n architecture.

### 10.3 Micro YOLO at 128×128

This was trained using:

```python
model = YOLO("/kaggle/working/yolov8_digits_micro.yaml")

model.train(
    data=DATA_YAML,
    epochs=250,
    imgsz=128,
    batch=64,
    patience=50,
    device=0,
    workers=2,
    project="/kaggle/working/runs_digit_detector",
    name="yolov8_digits_micro_128",
    pretrained=False,
    optimizer="AdamW",
    lr0=0.002,
    cos_lr=True,
    warmup_epochs=5,
    mosaic=0.4,
    close_mosaic=40,
    plots=True
)
```

Purpose:

```text
Test the smallest practical embedded YOLO digit detector.
```

Limitation:

```text
128×128 may lose small digit details.
```

### 10.4 Final preferred model: micro YOLO at 160×160

The final preferred training direction was:

```python
model = YOLO("/kaggle/working/yolov8_digits_micro.yaml")

model.train(
    data=DATA_YAML,
    epochs=250,
    imgsz=160,
    batch=64,
    patience=50,
    device=0,
    workers=2,
    project="/kaggle/working/runs_digit_detector",
    name="yolov8_digits_micro_160",
    pretrained=False,
    optimizer="AdamW",
    lr0=0.002,
    cos_lr=True,
    warmup_epochs=5,
    mosaic=0.35,
    close_mosaic=40,
    plots=True
)
```

Why 160 was used:

```text
320×320 was more accurate but too heavy.
128×128 was lighter but lost some digit detail.
160×160 gave a better balance for ESP32-CAM deployment.
```

---

## 11. Exporting YOLO to TFLite

The selected micro YOLO model was exported using Ultralytics:

```python
micro_model = YOLO("/kaggle/working/runs_digit_detector/yolov8_digits_micro_160/weights/best.pt")

exported = micro_model.export(
    format="tflite",
    imgsz=160,
    int8=True,
    data=DATA_YAML
)
```

The important output files are usually inside:

```text
/kaggle/working/runs_digit_detector/yolov8_digits_micro_160/weights/best_saved_model/
```

Possible exported files:

```text
best_float32.tflite
best_float16.tflite
best_int8.tflite
best_full_integer_quant.tflite
best_integer_quant.tflite
```

The final embedded direction used the full-integer/int8 TFLite model.

Recommended file to keep in the repository:

```text
models/yolo_digit_detector/best_full_integer_quant.tflite
```

or the exact `.tflite` file used by the final sketch.

---

## 12. Adding YOLO TFLite model to the ESP32-CAM sketch

The ESP32-CAM sketch cannot directly load a random file from Kaggle unless the code is designed to read it from storage.

The usual embedded approach is:

```text
TFLite file
    ↓
convert to C array/header file
    ↓
include it in Arduino sketch
    ↓
load model from memory
```

Example conversion command on Linux/macOS:

```bash
xxd -i best_full_integer_quant.tflite > yolo_model_data.h
```

On Windows, use one of:

```text
Git Bash xxd
WSL
Python conversion script
online binary-to-C-array tool
```

Example Python converter:

```python
from pathlib import Path

model_path = Path("best_full_integer_quant.tflite")
data = model_path.read_bytes()

with open("yolo_model_data.h", "w") as f:
    f.write("#pragma once\n")
    f.write("#include <cstdint>\n\n")
    f.write(f"const unsigned char yolo_model_data[] = {{\n")

    for i, b in enumerate(data):
        if i % 12 == 0:
            f.write("  ")
        f.write(f"0x{b:02x}, ")
        if i % 12 == 11:
            f.write("\n")

    f.write("\n};\n")
    f.write(f"const unsigned int yolo_model_data_len = {len(data)};\n")
```

Then include in Arduino:

```cpp
#include "yolo_model_data.h"
```

The sketch then creates/interprets the model using the TFLite Micro-compatible interpreter.

---

## 13. Letterbox preprocessing

YOLO expects a fixed square input size:

```text
160×160
```

But the LCD crop is rectangular.

Direct resize would distort the digits, so the final code uses **letterbox preprocessing**:

```text
Resize while preserving aspect ratio
Add padding to reach 160×160
```

This keeps digit shapes closer to the training data.

If the model input size changes, update both:

```text
training image size
export image size
Arduino preprocessing size
YOLO output decoding assumptions
```

Example:

```cpp
#define YOLO_INPUT_W 160
#define YOLO_INPUT_H 160
```

---

## 14. YOLO post-processing in the final sketch

After YOLO inference, the final sketch performs post-processing:

```text
1. Decode model output.
2. Remove detections below confidence threshold.
3. Apply row filtering to keep the main digit row.
4. Sort boxes by x-position.
5. Convert class IDs to characters.
6. Build final reading string.
```

Classes:

```cpp
const char* CLASS_NAMES[] = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."
};
```

Recommended confidence threshold:

```cpp
#define YOLO_CONF_THRESH 0.15f
```

If false digits appear, try:

```cpp
#define YOLO_CONF_THRESH 0.20f
```

Do not increase it too much because some real digits may have lower confidence.

---

## 15. Burst capture and final selection

The final implementation uses burst capture.

Purpose:

```text
Reduce dependency on a single bad frame.
```

Flow:

```text
Capture frame 1 → read digits
Capture frame 2 → read digits
Compare results
Choose final reading
```

The scoring may consider:

```text
reading validity
average confidence
number of detections
whether status is OK
whether the reading length is reasonable
```

Suggested future improvement:

```cpp
if (reading.length() > 8) score -= 0.50f;
```

This helps reject frames with an extra false leading digit.

---

## 16 Final ESP32-CAM sketch configuration reference

The important constants in `esp32cam_chirale_fomo_yolo_uart_v4_burst.ino` are listed below so they can be tuned in the system without rewriting the code.

### Debug and storage

```cpp
#define USE_SD_DEBUG          1
#define USE_BUTTONS           1
#define SAVE_FULL_JPG         1
#define SAVE_CROP_BMP         1
#define SAVE_MODEL_INPUT_BMP  1
```

The current implementation uses the SD card for debug logs and saved images. If SD instability happens, disable the debug saves first, or set `USE_BUTTONS` back to `0` because GPIO12/GPIO13 can conflict with SD card pins on the AI-Thinker ESP32-CAM but right now they are not causing any conflicts.

### Camera and burst capture

```cpp
#define CAMERA_FRAME_SIZE     FRAMESIZE_VGA   //640*480
#define CAMERA_JPEG_QUALITY   10
#define WARMUP_FRAMES         3
#define BURST_CAPTURE_COUNT   2
#define BURST_GAP_MS          120
```

`WARMUP_FRAMES = 3` discards three camera frames before capture to stabilize exposure. `BURST_CAPTURE_COUNT = 2` captures two frames quickly, then performs inference on both and chooses the best result.

### FOMO input and crop tuning

```cpp
static const int FOMO_IN_W = 96;
static const int FOMO_IN_H = 96;
static const int FOMO_GRID_W = 12;
static const int FOMO_GRID_H = 12;
static const float FOMO_CONF_THRESH = 0.70f;
static const bool FOMO_USE_FIT_SHORTEST = true;

static const float FOMO_CROP_W_RATIO = 0.55f;
static const float FOMO_CROP_H_RATIO = 0.18f;
static const float FOMO_SHIFT_X_RATIO = 0.07f;
static const float FOMO_SHIFT_Y_RATIO = 0.01f;
```

To make the FOMO crop wider, increase `FOMO_CROP_W_RATIO`. To make it taller, increase `FOMO_CROP_H_RATIO`. To move the crop right/left, tune `FOMO_SHIFT_X_RATIO`. To move it down/up, tune `FOMO_SHIFT_Y_RATIO`.

### Fixed crop fallback tuning

If FOMO fails, the sketch can use a fixed crop fallback:

```cpp
static const bool USE_FIXED_CROP_FALLBACK = true;
#define USE_ABSOLUTE_CROP     1
#define CROP_X1_ABS           220
#define CROP_Y1_ABS           95
#define CROP_X2_ABS           640
#define CROP_Y2_ABS           275
```

To tune the fixed crop, inspect the saved `/full_XXXX.jpg` and `/crop_XXXX.bmp` files on the SD card and adjust these four absolute coordinates.

### YOLO model settings

```cpp
static const int YOLO_IN_W = 160;
static const int YOLO_IN_H = 160;
static const int YOLO_NUM_BOXES = 1600;
static const int YOLO_NUM_CLASSES = 11;
static float YOLO_CONF_THRESH = 0.20f;
static bool YOLO_USE_STRETCH = false;
static int YOLO_OUTPUT_LAYOUT = 0;
static bool YOLO_BOXES_NORMALIZED = true;
static float YOLO_NMS_THRESH  = 0.45f;
static const float YOLO_ROW_GROUP_THRESH = 28.0f;
```

`YOLO_USE_STRETCH = false` means the final sketch uses letterbox preprocessing, not direct stretching. The output is forced as channel-first `[1, 15, 1600]`, with normalized boxes scaled to 160×160.

### Tensor arenas

```cpp
static const size_t FOMO_TENSOR_ARENA_SIZE = 400 * 1024;
static const size_t TENSOR_ARENA_SIZE = 2500 * 1024;
```

The FOMO model uses a 400 KB arena. The YOLO model uses a 2.5 MB arena in PSRAM. PSRAM must be enabled.

### Serial commands

Open the Serial Monitor at 115200 baud. The sketch supports:

```text
c or C  → capture/read/send result
l or L  → toggle flash LED
m or M  → toggle YOLO preprocessing mode between letterbox and stretch
+       → increase YOLO confidence threshold by 0.05
-       → decrease YOLO confidence threshold by 0.05
button on gpio 12 → capture 
button on gpio 13 → led on or off
```

## 17. Running the final ESP32-CAM code

### 17.1 Before running

Check:

```text
microSD card inserted
camera connected properly
ESP32-CAM powered by stable 5V
PSRAM enabled
correct board selected
FOMO model header included
YOLO model header included
UART wires connected if using LilyGO
```

### 17.2 Expected serial behavior

Typical output should show:

```text
Camera initialized
SD card initialized
FOMO inference started
LCD crop saved / crop computed
YOLO inference started
Detections decoded
FRAME 1 reading=...
FRAME 2 reading=...
FINAL BURST reading=...
STATUS=OK
UART sent
```

If the output shows `STATUS=FAIL`, check:

```text
camera capture failed
SD card failed
FOMO did not detect screen
crop is wrong
YOLO model failed to invoke
not enough detections
UART wiring issue
```

---

## 18. LilyGO TX / display / forwarding code

The LilyGO sketch receives the final reading from the ESP32-CAM over UART.

Expected behavior:

```text
Wait for UART message
Parse final reading/status
Display reading on screen
Optionally forward using LoRa
```

Typical UART message can be:

```text
READING=000589;STATUS=OK
```

or:

```text
FINAL BURST reading=000589 STATUS=OK
```



---

## 19. LilyGO RX / LoRa receiver code

The RX code listens for LoRa packets and prints/displays the received reading.

Expected packet content:

```text
meter_id
reading
status
optional timestamp
```

This node receives LoRa packets from the transmitter and forwards them to a dashboard over WiFi using MQTT. No additional libraries are needed beyond those already installed for the transmitter. 

### Configuration

Before flashing, update your WiFi credentials and MQTT server address in the code:

```cpp
const char* ssid        = "your_wifi_name";
const char* password    = "your_wifi_password";
const char* mqtt_server = "10.122.219.178"; // Your local machine's IP or ThingsBoard URL
const int   mqtt_port   = 1883;
```
If you are running it locally, make sure your machine is running some kind of MQTT broker, such as mosquitto. 

---

### Option A — Local MQTT Broker + Dashboard

Data is published to a local MQTT broker running on your machine, and a Python dashboard reads and displays it.

**To run the dashboard:**
1. Navigate to the `dashboard/` folder
2. Create a virtual environment: `python -m venv .venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Open two terminals and run:
   - `python backend.py`
   - `python frontend.py`
5. Open your browser and go to `http://localhost:8501`

---

### Option B — ThingsBoard (Cloud MQTT Broker)

If you prefer to use ThingsBoard instead of a local broker, a few small code changes are required.

**1. Add your ThingsBoard device token:**
```cpp
const char* TOKEN = "YOUR_DEVICE_TOKEN_HERE"; // From your ThingsBoard device page
```

**2. Update `reconnectMQTT()` to authenticate with the token:**
```cpp
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to ThingsBoard...\n");
    String clientId = "ALI-module-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), TOKEN, NULL)) {
      Serial.println("Connected to ThingsBoard!");
    } else {
      Serial.printf("✗ Failed. State=%d\n", client.state());
      delay(2000);
    }
  }
}
```

**3. Update every `client.publish()` call to use the ThingsBoard telemetry topic:**
```cpp
client.publish("v1/devices/me/telemetry", payload);
```

> ThingsBoard identifies the device by the token used to connect, so the topic is always the same regardless of which meter sent the data.

---

## 20. Known limitations

Current prototype limitations:

```text
1. Some seven-segment digits are visually similar.
   Common confusions: 2/5, 0/8, 3/9.

2. Real ESP32-CAM images are noisy and compressed.

3. Reflections or bad alignment may create false detections.

4. Burst selection can still choose a wrong frame if its confidence is higher.

5. Inference on ESP32-CAM is slow compared with laptop inference.

6. Camera placement must be stable for consistent results.
```

---

## 21. Suggested future improvements

```text
1. Add more ESP32-CAM real images to the YOLO training dataset.
2. Add more examples of confusing digit pairs: 2/5, 0/8, 3/9.
3. Improve burst scoring to penalize extra leading digits.
4. Add a fixed physical camera mount.
5. Optimize TFLite tensor arena and model size.
6. Add timestamp, meter ID, and checksum to LoRa packets.
7. Use a stronger ESP32-S3 board if faster inference is needed.
```

---

## 22. Suggested 3D printed camera mount

A stable camera position is important for reliable meter reading.

A suggested 3D-printable ESP32-CAM gas meter mount is available here:

```text
https://www.printables.com/model/322020-esp32-cam-gasmeter-g4-metrix
```

The model page describes an ESP32-CAM gas meter mounting system with variable length and angle.

This is only a suggested mechanical mounting reference. It may need modification depending on the actual meter shape, camera distance, and viewing angle.

---

## 23. Troubleshooting

### 23.1 ESP32-CAM upload fails

Check:

```text
GPIO0 connected to GND during upload
TX/RX are crossed
correct COM port selected
stable 5V power
press reset when "Connecting..." appears
```

### 23.2 ESP32-CAM boots into upload mode repeatedly

Cause:

```text
GPIO0 still connected to GND
```

Fix:

```text
Remove GPIO0 from GND and reset/power-cycle the board.
```

### 23.3 Camera capture fails

Check:

```text
AI Thinker ESP32-CAM board selected
camera pins match AI Thinker config
PSRAM enabled
stable power supply
camera ribbon cable seated correctly
```

### 23.4 SD card fails

Check:

```text
SD card inserted
FAT32 formatted
card not corrupted
SD_MMC pins not conflicting with other hardware
```

### 23.5 FOMO detects wrong crop

Fix:

```text
Add more screen images to Edge Impulse dataset
Check camera angle
Tune crop padding/margins
Use fixed crop fallback for demo
```

### 23.6 YOLO gives extra digits

Try:

```text
increase YOLO confidence threshold from 0.15 to 0.20
improve row filtering
penalize readings with too many digits
retrain with more negative examples/noisy crops
```

### 23.7 UART not received by LilyGO

Check:

```text
ESP32-CAM TX connected to LilyGO RX
GND shared between both boards
same baud rate in both sketches
correct UART pins in LilyGO code
message format matches parser
```

---

## 24. Short explanation 

This system is a working embedded prototype.  
The ESP32-CAM captures meter images, FOMO detects the LCD screen, the firmware dynamically crops the display, YOLO detects digits on the crop, and the final reading is sent to the LilyGO board through UART for display and LoRa forwarding.

The system was designed around ESP32-CAM constraints.  
Instead of running one large model on the full image, the project uses a hybrid approach:

```text
FOMO for lightweight screen localization
YOLO micro model for digit detection on the crop
post-processing for filtering and reading construction
UART/LoRa for communication
```

The main remaining improvements are dataset expansion, digit confusion reduction, and final burst-selection tuning.

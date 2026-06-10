/*
  ESP32-CAM Chirale FOMO screen crop + Chirale YOLO + UART packet V1

  Purpose:
    Run BOTH models with Chirale_TensorFlowLite only:
    1) raw exported Edge Impulse FOMO .tflite screen detector
    2) YOLO digit detector .tflite
    This avoids including smart-meter-screen-fomo_inferencing, so there are no duplicate TFLM symbols.

  Required files in the same sketch folder:
    - esp32cam_fixedcrop_chirale_yolo_uart.ino
    - digit_model_data_full_integer.h
    - fomo_model_data.h

  Required Arduino library:
    - Chirale_TensorFlowLite

  IMPORTANT:
    Disable/rename TensorFlowLite_ESP32 if Arduino accidentally includes it.
    Keep your LilyGO TX/RX code unchanged. It should listen for lines beginning with METER|.

  Controls:
    - Serial Monitor command 'c' or 'C'  -> capture/read/send result
    - Serial Monitor command 'l' or 'L'  -> toggle LED
    - Optional physical buttons are DISABLED by default when SD_MMC is used
      because GPIO12/GPIO13 are SD card pins on AI-Thinker ESP32-CAM.
*/

#include <Arduino.h>
#include <esp_camera.h>
#include <SD_MMC.h>
#include <FS.h>
#include <esp_heap_caps.h>
#include "img_converters.h"

#include "digit_model_data_full_integer.h"
#include "fomo_model_data.h"

#include <Chirale_TensorFlowLite.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"

// ─────────────────────────────────────────────────────────────
// AI-Thinker ESP32-CAM pins
// ─────────────────────────────────────────────────────────────
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ─────────────────────────────────────────────────────────────
// User config
// ─────────────────────────────────────────────────────────────
#define USE_SD_DEBUG          1
#define USE_BUTTONS           1   // V3: buttons re-enabled. If SD becomes unstable, set back to 0 and use Serial c/l.
#define SAVE_FULL_JPG         1
#define SAVE_CROP_BMP         1
#define SAVE_MODEL_INPUT_BMP  1

// Flash LED. On AI-Thinker ESP32-CAM this is usually GPIO4.
// If SD card causes issues, keep SD_MMC in 1-bit mode as below.
#define FLASH_LED_PIN         4

// Optional buttons. Disabled by default because AI-Thinker SD_MMC uses GPIO12/GPIO13.
// If you enable USE_BUTTONS, do NOT use SD_MMC with these pins. Prefer Serial commands: c and l.
#define CAPTURE_BUTTON_PIN    13
#define LED_BUTTON_PIN        12
#define BUTTON_ACTIVE_LOW     1

// UART output uses Serial/U0TXD GPIO1 by default.
// LilyGO TX board should connect its RX to ESP32-CAM GPIO1 and share GND.
#define SERIAL_BAUD           115200

// Camera settings
#define CAMERA_FRAME_SIZE     FRAMESIZE_VGA   // 640x480. Keep VGA for memory stability.
#define CAMERA_JPEG_QUALITY   10              // lower number = better quality/larger JPEG
#define WARMUP_FRAMES         3
#define LED_STABILIZE_MS      300

// Burst mode: capture the frames first, then run FOMO+YOLO on each saved JPEG.
// This avoids waiting ~14s between captures while the meter/hand position may change.
#define BURST_CAPTURE_COUNT   2      // 2 is safest for ESP32-CAM PSRAM. Try 3 only if stable.
#define BURST_GAP_MS          120    // small delay between quick captures


// FOMO screen model input/output from Edge Impulse export
static const int FOMO_IN_W = 96;
static const int FOMO_IN_H = 96;
static const int FOMO_GRID_W = 12;
static const int FOMO_GRID_H = 12;
static const int FOMO_CHANNELS = 2; // background + Reading class
static const float FOMO_CONF_THRESH = 0.70f;
static const float FOMO_OUT_SCALE = 0.00390625f;
static const int FOMO_OUT_ZERO = -128;
static const size_t FOMO_TENSOR_ARENA_SIZE = 400 * 1024;

// Edge Impulse project used "Fit shortest axis" for 640x480 -> 96x96 input.
// This means the image is resized so the short side becomes 96, then center-cropped.
static const bool FOMO_USE_FIT_SHORTEST = true;

// Dynamic LCD crop around FOMO center. These are your earlier Python ratios.
static const float FOMO_CROP_W_RATIO = 0.55f;
static const float FOMO_CROP_H_RATIO = 0.18f;
static const float FOMO_SHIFT_X_RATIO = 0.07f;
static const float FOMO_SHIFT_Y_RATIO = 0.01f;

// If FOMO fails, keep fixed crop as a fallback so the demo can still run.
static const bool USE_FIXED_CROP_FALLBACK = true;

// Fixed crop mode.
// For first testing with VGA 640x480, tune these ABS values from saved full/crop debug images.
// If USE_ABSOLUTE_CROP=0, ratios are used instead.
#define USE_ABSOLUTE_CROP     1

// Default wide LCD crop for VGA 640x480. Tune these after viewing /crop_xxxx.bmp.
// Make it safely wide at first, then tighten.
#define CROP_X1_ABS           220
#define CROP_Y1_ABS           95
#define CROP_X2_ABS           640
#define CROP_Y2_ABS           275

// Ratio fallback if USE_ABSOLUTE_CROP=0
#define CROP_X1_RATIO         0.34f
#define CROP_Y1_RATIO         0.20f
#define CROP_X2_RATIO         1.00f
#define CROP_Y2_RATIO         0.57f

// YOLO input/output
static const int YOLO_IN_W = 160;
static const int YOLO_IN_H = 160;
static const int YOLO_NUM_BOXES = 1600;
static const int YOLO_NUM_CLASSES = 11;
static const int YOLO_NUM_CHANNELS = 15; // 4 box + 11 classes
static const char *CLASS_NAMES[YOLO_NUM_CLASSES] = {
  "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."
};

// Match your Kaggle test as starting point.
static float YOLO_CONF_THRESH = 0.20f;

// IMPORTANT DEBUG SWITCH:
// 0 = Ultralytics-style letterbox to 160x160 with gray padding.
// 1 = stretch crop directly to 160x160.
// If Kaggle detects on crop_000x.bmp but ESP detects nothing, try stretch first.
static bool YOLO_USE_STRETCH = false;  // v3: default LETTERBOX to match Ultralytics/Kaggle preprocessing

// YOLO output decode debug:
// layout 0 = channel-first: out[ch][box]  (typical [1,15,1600])
// layout 1 = box-first:     out[box][ch]
// scale mode is auto-tested because some exports output xywh as 0..1 normalized.
static int YOLO_OUTPUT_LAYOUT = 0;      // FORCE channel-first [15][1600]
static bool YOLO_BOXES_NORMALIZED = true; // FORCE xywh normalized 0..1, scaled to 160

static float YOLO_NMS_THRESH  = 0.45f;
static const float YOLO_ROW_GROUP_THRESH = 28.0f; // keep one horizontal digit row after NMS
static const int MAX_CANDIDATES = 120;
static const int MAX_DETECTIONS = 16;

// Chirale YOLO standalone test succeeded with 2.5 MB arena.
static const size_t TENSOR_ARENA_SIZE = 2500 * 1024;

// ─────────────────────────────────────────────────────────────
// Structs/global state
// ─────────────────────────────────────────────────────────────
struct CropRect {
  int x1, y1, x2, y2;
};

struct Detection {
  int cls;
  float conf;
  float cx, cy, w, h;
  float x1, y1, x2, y2;
};

static bool sdReady = false;
static bool ledOn = false;
static int saveCounter = 0;
static uint32_t lastCaptureButtonMs = 0;
static uint32_t lastLedButtonMs = 0;
static bool lastCaptureButtonState = HIGH;
static bool lastLedButtonState = HIGH;

static const tflite::Model *model = nullptr;
static tflite::MicroInterpreter *interpreter = nullptr;
static TfLiteTensor *input = nullptr;
static TfLiteTensor *output = nullptr;
static uint8_t *tensor_arena = nullptr;

static const tflite::Model *fomoModel = nullptr;
static tflite::MicroInterpreter *fomoInterpreter = nullptr;
static TfLiteTensor *fomoInput = nullptr;
static TfLiteTensor *fomoOutput = nullptr;
static uint8_t *fomoTensorArena = nullptr;

struct FomoBox {
  int inputX;
  int inputY;
  int inputW;
  int inputH;
  int fullCx;
  int fullCy;
  float conf;
};

struct CaptureCopy {
  int id;
  bool ok;
  uint8_t *jpg;
  size_t len;
  int w;
  int h;

  CaptureCopy() : id(0), ok(false), jpg(nullptr), len(0), w(0), h(0) {}
};

struct FrameResult {
  int id;
  bool ok;
  String reading;
  float avgConf;
  int detCount;
  String status;
  float score;

  FrameResult() : id(0), ok(false), reading(""), avgConf(0.0f), detCount(0), status("INIT"), score(-999.0f) {}
};

// V3: keep large detection buffers global/static instead of local stack.
// The previous version could trigger: Stack canary watchpoint triggered (loopTask)
// after Invoke(), especially when decoding output.
static Detection g_candidates[MAX_CANDIDATES];
static Detection g_kept[MAX_DETECTIONS];

// ─────────────────────────────────────────────────────────────
// Small helpers
// ─────────────────────────────────────────────────────────────
static int clampi(int v, int lo, int hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

static void setLed(bool on) {
  ledOn = on;
  digitalWrite(FLASH_LED_PIN, ledOn ? HIGH : LOW);
}

static void appendLogC(const char *line) {
#if USE_SD_DEBUG
  if (!sdReady || line == nullptr) return;
  File f = SD_MMC.open("/log.txt", FILE_APPEND);
  if (!f) return;
  f.println(line);
  f.close();
#endif
}

static void appendLogToSD(const String &line) {
  appendLogC(line.c_str());
}

static void logLine(const String &line) {
  Serial.println(line);
  appendLogToSD(line);
}

static void logf(const char *fmt, ...) {
  char buf[256];
  va_list args;
  va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args);
  va_end(args);
  logLine(String(buf));
}

static bool saveBytesToSD(const char *path, const uint8_t *data, size_t len) {
#if USE_SD_DEBUG
  if (!sdReady) return false;
  File f = SD_MMC.open(path, FILE_WRITE);
  if (!f) {
    logf("SD open failed: %s", path);
    return false;
  }
  size_t written = f.write(data, len);
  f.close();
  if (written != len) {
    logf("SD short write: %s wrote=%u len=%u", path, (unsigned)written, (unsigned)len);
    return false;
  }
  logf("Saved %s (%u bytes)", path, (unsigned)len);
  return true;
#else
  return false;
#endif
}

static void writeLE16(File &f, uint16_t v) {
  f.write((uint8_t)(v & 0xFF));
  f.write((uint8_t)((v >> 8) & 0xFF));
}

static void writeLE32(File &f, uint32_t v) {
  f.write((uint8_t)(v & 0xFF));
  f.write((uint8_t)((v >> 8) & 0xFF));
  f.write((uint8_t)((v >> 16) & 0xFF));
  f.write((uint8_t)((v >> 24) & 0xFF));
}

// Save RGB888 buffer crop as BMP. rgb is full image RGB888 with stride fullW.
static bool saveBmpCropRGB888(const char *path, const uint8_t *rgb, int fullW, int fullH, CropRect crop) {
#if USE_SD_DEBUG
  if (!sdReady) return false;

  crop.x1 = clampi(crop.x1, 0, fullW - 1);
  crop.x2 = clampi(crop.x2, crop.x1 + 1, fullW);
  crop.y1 = clampi(crop.y1, 0, fullH - 1);
  crop.y2 = clampi(crop.y2, crop.y1 + 1, fullH);

  int w = crop.x2 - crop.x1;
  int h = crop.y2 - crop.y1;
  int rowSize = (w * 3 + 3) & ~3;
  uint32_t imageSize = rowSize * h;
  uint32_t fileSize = 54 + imageSize;

  File f = SD_MMC.open(path, FILE_WRITE);
  if (!f) {
    logf("BMP open failed: %s", path);
    return false;
  }

  // BMP header
  f.write('B'); f.write('M');
  writeLE32(f, fileSize);
  writeLE16(f, 0); writeLE16(f, 0);
  writeLE32(f, 54);
  writeLE32(f, 40);
  writeLE32(f, w);
  writeLE32(f, h);
  writeLE16(f, 1);
  writeLE16(f, 24);
  writeLE32(f, 0);
  writeLE32(f, imageSize);
  writeLE32(f, 2835); writeLE32(f, 2835);
  writeLE32(f, 0); writeLE32(f, 0);

  uint8_t pad[3] = {0, 0, 0};
  int padLen = rowSize - w * 3;

  // bottom-up BMP, BGR order
  for (int yy = h - 1; yy >= 0; yy--) {
    int sy = crop.y1 + yy;
    for (int xx = 0; xx < w; xx++) {
      int sx = crop.x1 + xx;
      size_t idx = (sy * fullW + sx) * 3;
      uint8_t r = rgb[idx + 0];
      uint8_t g = rgb[idx + 1];
      uint8_t b = rgb[idx + 2];
      f.write(b); f.write(g); f.write(r);
    }
    if (padLen) f.write(pad, padLen);
  }

  f.close();
  logf("Saved %s (%dx%d BMP)", path, w, h);
  return true;
#else
  return false;
#endif
}

// Save the current YOLO input tensor as BMP for checking letterbox/crop.
static bool saveYoloInputBmp(const char *path) {
#if USE_SD_DEBUG
  if (!sdReady || !input) return false;

  int w = YOLO_IN_W;
  int h = YOLO_IN_H;
  int rowSize = (w * 3 + 3) & ~3;
  uint32_t imageSize = rowSize * h;
  uint32_t fileSize = 54 + imageSize;

  File f = SD_MMC.open(path, FILE_WRITE);
  if (!f) {
    logf("YOLO BMP open failed: %s", path);
    return false;
  }

  f.write('B'); f.write('M');
  writeLE32(f, fileSize);
  writeLE16(f, 0); writeLE16(f, 0);
  writeLE32(f, 54);
  writeLE32(f, 40);
  writeLE32(f, w);
  writeLE32(f, h);
  writeLE16(f, 1);
  writeLE16(f, 24);
  writeLE32(f, 0);
  writeLE32(f, imageSize);
  writeLE32(f, 2835); writeLE32(f, 2835);
  writeLE32(f, 0); writeLE32(f, 0);

  uint8_t pad[3] = {0, 0, 0};
  int padLen = rowSize - w * 3;

  for (int yy = h - 1; yy >= 0; yy--) {
    for (int xx = 0; xx < w; xx++) {
      size_t idx = (yy * w + xx) * 3;
      uint8_t r = 0, g = 0, b = 0;
      if (input->type == kTfLiteInt8) {
        float rf = (input->data.int8[idx + 0] - input->params.zero_point) * input->params.scale;
        float gf = (input->data.int8[idx + 1] - input->params.zero_point) * input->params.scale;
        float bf = (input->data.int8[idx + 2] - input->params.zero_point) * input->params.scale;
        r = (uint8_t)clampi((int)roundf(rf * 255.0f), 0, 255);
        g = (uint8_t)clampi((int)roundf(gf * 255.0f), 0, 255);
        b = (uint8_t)clampi((int)roundf(bf * 255.0f), 0, 255);
      } else if (input->type == kTfLiteUInt8) {
        float rf = (input->data.uint8[idx + 0] - input->params.zero_point) * input->params.scale;
        float gf = (input->data.uint8[idx + 1] - input->params.zero_point) * input->params.scale;
        float bf = (input->data.uint8[idx + 2] - input->params.zero_point) * input->params.scale;
        r = (uint8_t)clampi((int)roundf(rf * 255.0f), 0, 255);
        g = (uint8_t)clampi((int)roundf(gf * 255.0f), 0, 255);
        b = (uint8_t)clampi((int)roundf(bf * 255.0f), 0, 255);
      } else if (input->type == kTfLiteFloat32) {
        r = (uint8_t)clampi((int)roundf(input->data.f[idx + 0] * 255.0f), 0, 255);
        g = (uint8_t)clampi((int)roundf(input->data.f[idx + 1] * 255.0f), 0, 255);
        b = (uint8_t)clampi((int)roundf(input->data.f[idx + 2] * 255.0f), 0, 255);
      }
      f.write(b); f.write(g); f.write(r);
    }
    if (padLen) f.write(pad, padLen);
  }

  f.close();
  logf("Saved %s (160x160 YOLO input BMP)", path);
  return true;
#else
  return false;
#endif
}

// ─────────────────────────────────────────────────────────────
// Camera / SD / model init
// ─────────────────────────────────────────────────────────────
static bool initSD() {
#if USE_SD_DEBUG
  // 1-bit mode reduces conflicts on ESP32-CAM and keeps GPIO4 flash LED usable.
  if (!SD_MMC.begin("/sdcard", true)) {
    Serial.println("SD_MMC mount failed. Continuing without SD debug.");
    sdReady = false;
    return false;
  }
  uint8_t cardType = SD_MMC.cardType();
  if (cardType == CARD_NONE) {
    Serial.println("No SD card. Continuing without SD debug.");
    sdReady = false;
    return false;
  }
  sdReady = true;
  Serial.println("SD ready");
  return true;
#else
  sdReady = false;
  return false;
#endif
}

static bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = CAMERA_FRAME_SIZE;
  config.jpeg_quality = CAMERA_JPEG_QUALITY;
  config.fb_count = psramFound() ? 2 : 1;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    logf("Camera init failed: 0x%x", err);
    return false;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s) {
    s->set_brightness(s, 0);
    s->set_contrast(s, 1);
    s->set_saturation(s, -2);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_exposure_ctrl(s, 1);
    s->set_aec2(s, 1);
    s->set_gain_ctrl(s, 1);
    s->set_agc_gain(s, 5);
    s->set_vflip(s, 1);
    s->set_hmirror(s, 0);
    s->set_special_effect(s, 0); // normal color
  }

  logLine("Camera ready");
  return true;
}

static void printDims(const char *name, TfLiteTensor *t) {
  String dims = "";
  for (int i = 0; i < t->dims->size; i++) {
    dims += String(t->dims->data[i]);
    if (i < t->dims->size - 1) dims += ",";
  }
  logf("%s type=%d dims=%s scale=%.9f zero=%d bytes=%u",
       name, (int)t->type, dims.c_str(), t->params.scale, t->params.zero_point, (unsigned)t->bytes);
}


static bool initFomoModel() {
  fomoModel = tflite::GetModel(fomo_model_tflite);
  if (fomoModel->version() != TFLITE_SCHEMA_VERSION) {
    logf("FOMO schema %d != supported %d", fomoModel->version(), TFLITE_SCHEMA_VERSION);
    return false;
  }
  logLine("FOMO model schema OK");

  fomoTensorArena = (uint8_t *)heap_caps_malloc(FOMO_TENSOR_ARENA_SIZE, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
  if (!fomoTensorArena) {
    logLine("FOMO PSRAM arena allocation failed, trying heap...");
    fomoTensorArena = (uint8_t *)heap_caps_malloc(FOMO_TENSOR_ARENA_SIZE, MALLOC_CAP_8BIT);
  }
  if (!fomoTensorArena) {
    logLine("FOMO tensor arena allocation FAILED");
    return false;
  }
  logf("FOMO tensor arena allocated: %u bytes at %p", (unsigned)FOMO_TENSOR_ARENA_SIZE, fomoTensorArena);

  static tflite::AllOpsResolver fomoResolver;
  static tflite::MicroInterpreter static_fomo_interpreter(
      fomoModel, fomoResolver, fomoTensorArena, FOMO_TENSOR_ARENA_SIZE);
  fomoInterpreter = &static_fomo_interpreter;

  logLine("Calling FOMO AllocateTensors()...");
  TfLiteStatus alloc_status = fomoInterpreter->AllocateTensors();
  logf("FOMO AllocateTensors status=%d", (int)alloc_status);
  if (alloc_status != kTfLiteOk) {
    logLine("FOMO AllocateTensors FAILED");
    return false;
  }

  fomoInput = fomoInterpreter->input(0);
  fomoOutput = fomoInterpreter->output(0);
  printDims("FOMO Input", fomoInput);
  printDims("FOMO Output", fomoOutput);
  logLine("FOMO model ready");
  return true;
}

static bool initYoloModel() {
  model = tflite::GetModel(digit_model_tflite);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    logf("Model schema %d != supported %d", model->version(), TFLITE_SCHEMA_VERSION);
    return false;
  }
  logLine("Model schema OK");

  tensor_arena = (uint8_t *)heap_caps_malloc(TENSOR_ARENA_SIZE, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
  if (!tensor_arena) {
    logLine("PSRAM tensor arena allocation failed, trying normal heap...");
    tensor_arena = (uint8_t *)heap_caps_malloc(TENSOR_ARENA_SIZE, MALLOC_CAP_8BIT);
  }
  if (!tensor_arena) {
    logLine("Tensor arena allocation FAILED");
    return false;
  }
  logf("Tensor arena allocated: %u bytes at %p", (unsigned)TENSOR_ARENA_SIZE, tensor_arena);

  static tflite::AllOpsResolver resolver;
  static tflite::MicroInterpreter static_interpreter(
      model, resolver, tensor_arena, TENSOR_ARENA_SIZE);
  interpreter = &static_interpreter;

  logLine("Calling AllocateTensors()...");
  TfLiteStatus alloc_status = interpreter->AllocateTensors();
  logf("AllocateTensors status=%d", (int)alloc_status);
  if (alloc_status != kTfLiteOk) {
    logLine("AllocateTensors FAILED");
    return false;
  }

  input = interpreter->input(0);
  output = interpreter->output(0);
  printDims("Input", input);
  printDims("Output", output);
  logLine("YOLO model ready");
  return true;
}

// ─────────────────────────────────────────────────────────────
// YOLO crop/input/decode
// ─────────────────────────────────────────────────────────────

static uint8_t rgbToGray(const uint8_t *p) {
  // p is RGB888
  return (uint8_t)((77 * p[0] + 150 * p[1] + 29 * p[2]) >> 8);
}

static bool fillFomoInputFromRGB(const uint8_t *fullRgb, int fullW, int fullH,
                                 float &scale, int &cropOffX, int &cropOffY,
                                 int &resizedW, int &resizedH) {
  if (!fomoInput || fomoInput->type != kTfLiteInt8) {
    logLine("FOMO input missing or not INT8");
    return false;
  }

  if (FOMO_USE_FIT_SHORTEST) {
    scale = max((float)FOMO_IN_W / fullW, (float)FOMO_IN_H / fullH);
  } else {
    scale = 0.0f; // stretch mode
  }

  if (FOMO_USE_FIT_SHORTEST) {
    resizedW = max(1, (int)roundf(fullW * scale));
    resizedH = max(1, (int)roundf(fullH * scale));
    cropOffX = max(0, (resizedW - FOMO_IN_W) / 2);
    cropOffY = max(0, (resizedH - FOMO_IN_H) / 2);
  } else {
    resizedW = FOMO_IN_W;
    resizedH = FOMO_IN_H;
    cropOffX = 0;
    cropOffY = 0;
  }

  int8_t *dst = fomoInput->data.int8;
  const float inScale = fomoInput->params.scale;
  const int inZero = fomoInput->params.zero_point;

  for (int y = 0; y < FOMO_IN_H; y++) {
    for (int x = 0; x < FOMO_IN_W; x++) {
      float srcXf, srcYf;
      if (FOMO_USE_FIT_SHORTEST) {
        srcXf = (x + cropOffX + 0.5f) / scale - 0.5f;
        srcYf = (y + cropOffY + 0.5f) / scale - 0.5f;
      } else {
        srcXf = (x + 0.5f) * fullW / (float)FOMO_IN_W - 0.5f;
        srcYf = (y + 0.5f) * fullH / (float)FOMO_IN_H - 0.5f;
      }

      int sx = clampi((int)roundf(srcXf), 0, fullW - 1);
      int sy = clampi((int)roundf(srcYf), 0, fullH - 1);
      const uint8_t *pix = &fullRgb[(sy * fullW + sx) * 3];
      float gray01 = rgbToGray(pix) / 255.0f;
      int q = (int)roundf(gray01 / inScale) + inZero;
      q = clampi(q, -128, 127);
      dst[y * FOMO_IN_W + x] = (int8_t)q;
    }
  }

  logf("FOMO input mode=%s resized=%dx%d off=%d,%d scale=%.4f",
       FOMO_USE_FIT_SHORTEST ? "FIT_SHORTEST" : "STRETCH",
       resizedW, resizedH, cropOffX, cropOffY, scale);
  return true;
}

static void mapFomoInputToFull(int ix, int iy, int fullW, int fullH,
                               float scale, int cropOffX, int cropOffY,
                               int &fx, int &fy) {
  if (FOMO_USE_FIT_SHORTEST) {
    fx = clampi((int)roundf((ix + cropOffX) / scale), 0, fullW - 1);
    fy = clampi((int)roundf((iy + cropOffY) / scale), 0, fullH - 1);
  } else {
    fx = clampi((int)roundf(ix * fullW / (float)FOMO_IN_W), 0, fullW - 1);
    fy = clampi((int)roundf(iy * fullH / (float)FOMO_IN_H), 0, fullH - 1);
  }
}

static bool runFomoFromRGB(const uint8_t *fullRgb, int fullW, int fullH, FomoBox &best) {
  best.conf = 0.0f;
  best.inputX = best.inputY = best.inputW = best.inputH = 0;
  best.fullCx = fullW / 2;
  best.fullCy = fullH / 2;

  float scale = 1.0f;
  int cropOffX = 0, cropOffY = 0, resizedW = FOMO_IN_W, resizedH = FOMO_IN_H;
  if (!fillFomoInputFromRGB(fullRgb, fullW, fullH, scale, cropOffX, cropOffY, resizedW, resizedH)) {
    return false;
  }

  logf("Before FOMO Invoke: freeHeap=%u freePsram=%u", ESP.getFreeHeap(), ESP.getFreePsram());
  uint32_t t0 = millis();
  TfLiteStatus st = fomoInterpreter->Invoke();
  uint32_t dt = millis() - t0;
  logf("FOMO Invoke status=%d time_ms=%u", (int)st, (unsigned)dt);
  if (st != kTfLiteOk) return false;

  if (!fomoOutput || fomoOutput->type != kTfLiteInt8) {
    logLine("FOMO output missing or not INT8");
    return false;
  }

  int above = 0;
  for (int gy = 0; gy < FOMO_GRID_H; gy++) {
    for (int gx = 0; gx < FOMO_GRID_W; gx++) {
      int loc = ((gy * FOMO_GRID_W) + gx) * FOMO_CHANNELS;
      int8_t q = fomoOutput->data.int8[loc + 1]; // channel 1 = Reading class
      float conf = (q - FOMO_OUT_ZERO) * FOMO_OUT_SCALE;
      if (conf >= FOMO_CONF_THRESH) above++;
      if (conf > best.conf) {
        best.conf = conf;
        best.inputX = gx * (FOMO_IN_W / FOMO_GRID_W);
        best.inputY = gy * (FOMO_IN_H / FOMO_GRID_H);
        best.inputW = (FOMO_IN_W / FOMO_GRID_W);
        best.inputH = (FOMO_IN_H / FOMO_GRID_H);
        int icx = best.inputX + best.inputW / 2;
        int icy = best.inputY + best.inputH / 2;
        mapFomoInputToFull(icx, icy, fullW, fullH, scale, cropOffX, cropOffY, best.fullCx, best.fullCy);
      }
    }
  }

  logf("FOMO best input=[%d,%d,%d,%d] fullCenter=(%d,%d) conf=%.3f above=%d",
       best.inputX, best.inputY, best.inputW, best.inputH, best.fullCx, best.fullCy, best.conf, above);
  return best.conf >= FOMO_CONF_THRESH;
}

static CropRect getFomoCrop(const FomoBox &fbx, int fullW, int fullH) {
  int cropW = (int)roundf(fullW * FOMO_CROP_W_RATIO);
  int cropH = (int)roundf(fullH * FOMO_CROP_H_RATIO);
  int cx = fbx.fullCx + (int)roundf(fullW * FOMO_SHIFT_X_RATIO);
  int cy = fbx.fullCy + (int)roundf(fullH * FOMO_SHIFT_Y_RATIO);

  CropRect c;
  c.x1 = cx - cropW / 2;
  c.x2 = c.x1 + cropW;
  c.y1 = cy - cropH / 2;
  c.y2 = c.y1 + cropH;

  if (c.x1 < 0) { c.x2 -= c.x1; c.x1 = 0; }
  if (c.y1 < 0) { c.y2 -= c.y1; c.y1 = 0; }
  if (c.x2 > fullW) { int d = c.x2 - fullW; c.x1 -= d; c.x2 = fullW; }
  if (c.y2 > fullH) { int d = c.y2 - fullH; c.y1 -= d; c.y2 = fullH; }

  c.x1 = clampi(c.x1, 0, fullW - 1);
  c.y1 = clampi(c.y1, 0, fullH - 1);
  c.x2 = clampi(c.x2, c.x1 + 1, fullW);
  c.y2 = clampi(c.y2, c.y1 + 1, fullH);
  return c;
}

static CropRect getFixedCrop(int fullW, int fullH) {
  CropRect c;
#if USE_ABSOLUTE_CROP
  c.x1 = CROP_X1_ABS;
  c.y1 = CROP_Y1_ABS;
  c.x2 = CROP_X2_ABS;
  c.y2 = CROP_Y2_ABS;
#else
  c.x1 = (int)roundf(CROP_X1_RATIO * fullW);
  c.y1 = (int)roundf(CROP_Y1_RATIO * fullH);
  c.x2 = (int)roundf(CROP_X2_RATIO * fullW);
  c.y2 = (int)roundf(CROP_Y2_RATIO * fullH);
#endif
  c.x1 = clampi(c.x1, 0, fullW - 1);
  c.y1 = clampi(c.y1, 0, fullH - 1);
  c.x2 = clampi(c.x2, c.x1 + 1, fullW);
  c.y2 = clampi(c.y2, c.y1 + 1, fullH);
  return c;
}

static bool fillYoloInputFromRGB(const uint8_t *fullRgb, int fullW, int fullH, CropRect crop) {
  int cropW = crop.x2 - crop.x1;
  int cropH = crop.y2 - crop.y1;
  if (cropW <= 0 || cropH <= 0) return false;

  // Two preprocessing modes:
  // 1) letterbox: keep aspect ratio and pad with 114
  // 2) stretch: resize crop directly to 160x160
  float resizeScale = min((float)YOLO_IN_W / cropW, (float)YOLO_IN_H / cropH);
  int newW = max(1, (int)roundf(cropW * resizeScale));
  int newH = max(1, (int)roundf(cropH * resizeScale));
  int padX = (YOLO_IN_W - newW) / 2;
  int padY = (YOLO_IN_H - newH) / 2;

  if (YOLO_USE_STRETCH) {
    resizeScale = 0.0f;
    newW = YOLO_IN_W;
    newH = YOLO_IN_H;
    padX = 0;
    padY = 0;
  }

  logf("Crop=[%d,%d,%d,%d] cropWH=%dx%d mode=%s new=%dx%d pad=%d,%d",
       crop.x1, crop.y1, crop.x2, crop.y2, cropW, cropH,
       YOLO_USE_STRETCH ? "STRETCH" : "LETTERBOX", newW, newH, padX, padY);

  if (input->type == kTfLiteInt8 || input->type == kTfLiteUInt8) {
    float qscale = input->params.scale;
    int zero = input->params.zero_point;
    int bgQ = (int)roundf((114.0f / 255.0f) / qscale) + zero;

    if (input->type == kTfLiteInt8) {
      bgQ = clampi(bgQ, -128, 127);
      memset(input->data.int8, (int8_t)bgQ, input->bytes);
    } else {
      bgQ = clampi(bgQ, 0, 255);
      memset(input->data.uint8, (uint8_t)bgQ, input->bytes);
    }

    for (int y = 0; y < newH; y++) {
      for (int x = 0; x < newW; x++) {
        int sx, sy;
        if (YOLO_USE_STRETCH) {
          sx = crop.x1 + (int)((float)x * cropW / YOLO_IN_W);
          sy = crop.y1 + (int)((float)y * cropH / YOLO_IN_H);
        } else {
          sx = crop.x1 + (int)((float)x / resizeScale);
          sy = crop.y1 + (int)((float)y / resizeScale);
        }
        sx = clampi(sx, crop.x1, crop.x2 - 1);
        sy = clampi(sy, crop.y1, crop.y2 - 1);

        size_t src = (sy * fullW + sx) * 3;
        int dx = padX + x;
        int dy = padY + y;
        size_t dst = (dy * YOLO_IN_W + dx) * 3;

        for (int ch = 0; ch < 3; ch++) {
          float v = fullRgb[src + ch] / 255.0f;
          int q = (int)roundf(v / qscale) + zero;
          if (input->type == kTfLiteInt8) input->data.int8[dst + ch] = (int8_t)clampi(q, -128, 127);
          else input->data.uint8[dst + ch] = (uint8_t)clampi(q, 0, 255);
        }
      }
    }
    return true;
  }

  if (input->type == kTfLiteFloat32) {
    float *in = input->data.f;
    for (int i = 0; i < YOLO_IN_W * YOLO_IN_H * 3; i++) in[i] = 114.0f / 255.0f;

    for (int y = 0; y < newH; y++) {
      for (int x = 0; x < newW; x++) {
        int sx, sy;
        if (YOLO_USE_STRETCH) {
          sx = crop.x1 + (int)((float)x * cropW / YOLO_IN_W);
          sy = crop.y1 + (int)((float)y * cropH / YOLO_IN_H);
        } else {
          sx = crop.x1 + (int)((float)x / resizeScale);
          sy = crop.y1 + (int)((float)y / resizeScale);
        }
        sx = clampi(sx, crop.x1, crop.x2 - 1);
        sy = clampi(sy, crop.y1, crop.y2 - 1);
        size_t src = (sy * fullW + sx) * 3;
        int dx = padX + x;
        int dy = padY + y;
        size_t dst = (dy * YOLO_IN_W + dx) * 3;
        in[dst + 0] = fullRgb[src + 0] / 255.0f;
        in[dst + 1] = fullRgb[src + 1] / 255.0f;
        in[dst + 2] = fullRgb[src + 2] / 255.0f;
      }
    }
    return true;
  }

  logf("Unsupported YOLO input type: %d", (int)input->type);
  return false;
}

static float outputValueLayout(int ch, int boxIdx, int layout) {
  int idx;
  if (layout == 0) {
    // channel-first: [15][1600]
    idx = ch * YOLO_NUM_BOXES + boxIdx;
  } else {
    // box-first: [1600][15]
    idx = boxIdx * YOLO_NUM_CHANNELS + ch;
  }

  if (idx < 0 || idx >= YOLO_NUM_CHANNELS * YOLO_NUM_BOXES) return 0.0f;

  if (output->type == kTfLiteInt8) {
    return (output->data.int8[idx] - output->params.zero_point) * output->params.scale;
  }
  if (output->type == kTfLiteUInt8) {
    return (output->data.uint8[idx] - output->params.zero_point) * output->params.scale;
  }
  if (output->type == kTfLiteFloat32) {
    return output->data.f[idx];
  }
  return 0.0f;
}

static float outputValue(int ch, int boxIdx) {
  return outputValueLayout(ch, boxIdx, YOLO_OUTPUT_LAYOUT);
}

static void printYoloStatsForLayout(int layout) {
  float maxClass = -999.0f;
  int maxClassIdx = -1;
  int maxClassCh = -1;

  float minBox[4] = { 999999.0f, 999999.0f, 999999.0f, 999999.0f };
  float maxBox[4] = { -999999.0f, -999999.0f, -999999.0f, -999999.0f };

  int classAbove = 0;
  int geomPassRaw = 0;
  int geomPassNormScaled = 0;

  for (int i = 0; i < YOLO_NUM_BOXES; i++) {
    for (int ch = 0; ch < 4; ch++) {
      float v = outputValueLayout(ch, i, layout);
      if (v < minBox[ch]) minBox[ch] = v;
      if (v > maxBox[ch]) maxBox[ch] = v;
    }

    float bestScore = -999.0f;
    int bestC = -1;
    for (int c = 0; c < YOLO_NUM_CLASSES; c++) {
      float s = outputValueLayout(4 + c, i, layout);
      if (s > bestScore) {
        bestScore = s;
        bestC = c;
      }
      if (s > maxClass) {
        maxClass = s;
        maxClassIdx = i;
        maxClassCh = c;
      }
    }

    if (bestScore >= YOLO_CONF_THRESH) {
      classAbove++;
      float cx = outputValueLayout(0, i, layout);
      float cy = outputValueLayout(1, i, layout);
      float w  = outputValueLayout(2, i, layout);
      float h  = outputValueLayout(3, i, layout);

      if (w > 1.0f && h > 1.0f && cx >= -20.0f && cx <= 180.0f && cy >= -20.0f && cy <= 180.0f && w <= 160.0f && h <= 160.0f) {
        geomPassRaw++;
      }

      float scx = cx * 160.0f;
      float scy = cy * 160.0f;
      float sw  = w  * 160.0f;
      float sh  = h  * 160.0f;
      if (sw > 1.0f && sh > 1.0f && scx >= -20.0f && scx <= 180.0f && scy >= -20.0f && scy <= 180.0f && sw <= 160.0f && sh <= 160.0f) {
        geomPassNormScaled++;
      }
    }
  }

  logf("YOLO L%d stats: maxClass=%.4f class=%s idx=%d classAbove=%.2f:%d geomRaw:%d geomNorm:%d",
       layout,
       maxClass,
       (maxClassCh >= 0 && maxClassCh < YOLO_NUM_CLASSES) ? CLASS_NAMES[maxClassCh] : "?",
       maxClassIdx,
       YOLO_CONF_THRESH,
       classAbove,
       geomPassRaw,
       geomPassNormScaled);
  logf("YOLO L%d boxes: cx %.4f..%.4f cy %.4f..%.4f w %.4f..%.4f h %.4f..%.4f",
       layout,
       minBox[0], maxBox[0], minBox[1], maxBox[1], minBox[2], maxBox[2], minBox[3], maxBox[3]);
}

static void printYoloOutputDebugStats() {
  printYoloStatsForLayout(0);
  printYoloStatsForLayout(1);
}

static int collectCandidatesForMode(int layout, bool normalizedBoxes) {
  int candCount = 0;

  for (int i = 0; i < YOLO_NUM_BOXES; i++) {
    int bestCls = -1;
    float bestScore = -999.0f;
    for (int c = 0; c < YOLO_NUM_CLASSES; c++) {
      float s = outputValueLayout(4 + c, i, layout);
      if (s > bestScore) {
        bestScore = s;
        bestCls = c;
      }
    }

    if (bestScore < YOLO_CONF_THRESH) continue;

    float cx = outputValueLayout(0, i, layout);
    float cy = outputValueLayout(1, i, layout);
    float w  = outputValueLayout(2, i, layout);
    float h  = outputValueLayout(3, i, layout);

    if (normalizedBoxes) {
      cx *= 160.0f;
      cy *= 160.0f;
      w  *= 160.0f;
      h  *= 160.0f;
    }

    // Basic sanity in 160x160 coordinates.
    if (w <= 1.0f || h <= 1.0f) continue;
    if (cx < -20.0f || cx > 180.0f || cy < -20.0f || cy > 180.0f) continue;
    if (w > 160.0f || h > 160.0f) continue;

    Detection dd;
    dd.cls = bestCls;
    dd.conf = bestScore;
    dd.cx = cx; dd.cy = cy; dd.w = w; dd.h = h;
    dd.x1 = cx - w / 2.0f;
    dd.y1 = cy - h / 2.0f;
    dd.x2 = cx + w / 2.0f;
    dd.y2 = cy + h / 2.0f;

    if (candCount < MAX_CANDIDATES) g_candidates[candCount++] = dd;
  }

  return candCount;
}

static float iou(const Detection &a, const Detection &b) {
  float xx1 = max(a.x1, b.x1);
  float yy1 = max(a.y1, b.y1);
  float xx2 = min(a.x2, b.x2);
  float yy2 = min(a.y2, b.y2);
  float iw = max(0.0f, xx2 - xx1);
  float ih = max(0.0f, yy2 - yy1);
  float inter = iw * ih;
  float areaA = max(0.0f, a.x2 - a.x1) * max(0.0f, a.y2 - a.y1);
  float areaB = max(0.0f, b.x2 - b.x1) * max(0.0f, b.y2 - b.y1);
  float uni = areaA + areaB - inter;
  if (uni <= 0.0f) return 0.0f;
  return inter / uni;
}

static void sortByConfDesc(Detection *d, int n) {
  for (int i = 0; i < n - 1; i++) {
    for (int j = i + 1; j < n; j++) {
      if (d[j].conf > d[i].conf) {
        Detection t = d[i]; d[i] = d[j]; d[j] = t;
      }
    }
  }
}

static void sortByCxAsc(Detection *d, int n) {
  for (int i = 0; i < n - 1; i++) {
    for (int j = i + 1; j < n; j++) {
      if (d[j].cx < d[i].cx) {
        Detection t = d[i]; d[i] = d[j]; d[j] = t;
      }
    }
  }
}


static int keepMainYRow(Detection *d, int n) {
  if (n <= 2) return n;

  float bestScore = -1.0f;
  int bestCount = 0;
  float bestCenterY = 0.0f;

  // Try each detection cy as a candidate row center.
  for (int i = 0; i < n; i++) {
    float sumConf = 0.0f;
    float sumCyWeighted = 0.0f;
    int count = 0;

    for (int j = 0; j < n; j++) {
      if (fabsf(d[j].cy - d[i].cy) <= YOLO_ROW_GROUP_THRESH) {
        sumConf += d[j].conf;
        sumCyWeighted += d[j].cy * d[j].conf;
        count++;
      }
    }

    // Prefer many detections, then high confidence.
    float score = (float)count * 2.0f + sumConf;
    if (score > bestScore) {
      bestScore = score;
      bestCount = count;
      bestCenterY = (sumConf > 0.0f) ? (sumCyWeighted / sumConf) : d[i].cy;
    }
  }

  Detection tmp[MAX_DETECTIONS];
  int out = 0;
  for (int i = 0; i < n && out < MAX_DETECTIONS; i++) {
    if (fabsf(d[i].cy - bestCenterY) <= YOLO_ROW_GROUP_THRESH) {
      tmp[out++] = d[i];
    }
  }

  for (int i = 0; i < out; i++) d[i] = tmp[i];
  logf("YOLO row filter: kept %d/%d detections around cy=%.1f", out, n, bestCenterY);
  return out;
}

static bool decodeYolo(String &reading, float &avgConf, int &detCount) {
  memset(g_candidates, 0, sizeof(g_candidates));
  memset(g_kept, 0, sizeof(g_kept));

  printYoloOutputDebugStats();

  // V6 IMPORTANT FIX:
  // The exported YOLO output tensor is [1, 15, 1600].
  // Correct interpretation is channel-first: output[channel][anchor].
  // Box values are normalized 0..1 and must be multiplied by 160.
  // V5 incorrectly auto-selected the mode with the MOST candidates, which chose
  // the wrong box-first layout and produced garbage detections.
  for (int layout = 0; layout <= 1; layout++) {
    for (int norm = 0; norm <= 1; norm++) {
      int count = collectCandidatesForMode(layout, norm == 1);
      logf("YOLO mode test: layout=%d normBoxes=%d candidates=%d", layout, norm, count);
    }
  }

  YOLO_OUTPUT_LAYOUT = 0;
  YOLO_BOXES_NORMALIZED = true;

  memset(g_candidates, 0, sizeof(g_candidates));
  int candCount = collectCandidatesForMode(YOLO_OUTPUT_LAYOUT, YOLO_BOXES_NORMALIZED);

  logf("YOLO FORCED decode: layout=0 normBoxes=1 raw candidates above %.2f: %d",
       YOLO_CONF_THRESH, candCount);

  if (candCount == 0) {
    logLine("decodeYolo: zero candidates, returning safely");
    return false;
  }

  sortByConfDesc(g_candidates, candCount);

  int keptCount = 0;
  for (int i = 0; i < candCount && keptCount < MAX_DETECTIONS; i++) {
    bool suppress = false;
    for (int j = 0; j < keptCount; j++) {
      if (iou(g_candidates[i], g_kept[j]) > YOLO_NMS_THRESH) {
        suppress = true;
        break;
      }
    }
    if (!suppress) g_kept[keptCount++] = g_candidates[i];
  }

  if (keptCount == 0) return false;

  keptCount = keepMainYRow(g_kept, keptCount);
  if (keptCount == 0) return false;

  sortByCxAsc(g_kept, keptCount);

  reading = "";
  avgConf = 0.0f;
  for (int i = 0; i < keptCount; i++) {
    reading += CLASS_NAMES[g_kept[i].cls];
    avgConf += g_kept[i].conf;
    logf("det %02d: %s conf=%.3f cx=%.1f cy=%.1f w=%.1f h=%.1f",
         i, CLASS_NAMES[g_kept[i].cls], g_kept[i].conf,
         g_kept[i].cx, g_kept[i].cy, g_kept[i].w, g_kept[i].h);
  }
  avgConf /= keptCount;
  detCount = keptCount;
  return reading.length() > 0;
}

// ─────────────────────────────────────────────────────────────
// Workflow
// ─────────────────────────────────────────────────────────────
static void discardWarmupFrames() {
  for (int i = 0; i < WARMUP_FRAMES; i++) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) esp_camera_fb_return(fb);
    delay(80);
  }
}

static void sendMeterPacket(const String &reading, float conf, const String &status) {
  // Use a fixed buffer instead of String concatenation to avoid heap fragmentation
  // after the long YOLO Invoke().
  char pkt[128];
  snprintf(pkt, sizeof(pkt), "METER|READING=%s|CONF=%.2f|STATUS=%s",
           reading.c_str(), conf, status.c_str());
  Serial.println(pkt);
  appendLogC(pkt);
}

static String classifyStatus(const String &reading, float avgConf, int detCount) {
  // Readings do NOT always have the same number of digits.
  // So do not reject 4-digit readings just because they are short.
  if (detCount <= 0 || reading.length() == 0) return "NO_DIGITS";
  if (detCount <= 2) return "FEW_DIGITS";
  if (detCount > 10) return "TOO_MANY";
  if (avgConf < 0.45f) return "LOW_CONF";
  return "OK";
}

static float qualityScore(const String &reading, float avgConf, int detCount, const String &status) {
  float s = avgConf;

  // Do not hard-code exact digit count, but heavily penalize clearly bad cases.
  if (detCount <= 2) s -= 0.80f;
  if (detCount > 10) s -= 0.40f;

  if (status == "OK") s += 0.35f;
  else if (status == "LOW_CONF") s -= 0.10f;
  else if (status == "FEW_DIGITS") s -= 0.35f;
  else if (status == "NO_DIGITS") s -= 1.00f;

  // Very tiny strings are usually bad unless the real meter is truly tiny-count.
  if (reading.length() <= 2) s -= 0.30f;

  return s;
}

static bool captureJpegCopy(CaptureCopy &cap, int id) {
  cap.id = id;
  cap.ok = false;
  cap.jpg = nullptr;
  cap.len = 0;
  cap.w = 0;
  cap.h = 0;

  discardWarmupFrames();
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    logf("Burst capture %d failed", id);
    return false;
  }

  cap.w = fb->width;
  cap.h = fb->height;
  cap.len = fb->len;
  cap.jpg = (uint8_t *)heap_caps_malloc(cap.len, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
  if (!cap.jpg) {
    // JPEGs are small; if PSRAM is fragmented, try heap as fallback.
    cap.jpg = (uint8_t *)heap_caps_malloc(cap.len, MALLOC_CAP_8BIT);
  }

  if (!cap.jpg) {
    logf("Burst capture %d copy allocation failed len=%u", id, (unsigned)fb->len);
    esp_camera_fb_return(fb);
    return false;
  }

  memcpy(cap.jpg, fb->buf, fb->len);
  logf("Burst captured %d: %dx%d len=%u", id, cap.w, cap.h, (unsigned)cap.len);

#if USE_SD_DEBUG && SAVE_FULL_JPG
  char fullPath[40];
  snprintf(fullPath, sizeof(fullPath), "/full_%04d.jpg", id);
  saveBytesToSD(fullPath, cap.jpg, cap.len);
#endif

  esp_camera_fb_return(fb);
  cap.ok = true;
  return true;
}

static void freeCapture(CaptureCopy &cap) {
  if (cap.jpg) free(cap.jpg);
  cap.jpg = nullptr;
  cap.len = 0;
  cap.ok = false;
}

static bool processCapturedJpeg(const CaptureCopy &cap, FrameResult &res) {
  res = FrameResult();
  res.id = cap.id;

  if (!cap.ok || !cap.jpg || cap.len == 0) {
    res.status = "CAPTURE_FAIL";
    return false;
  }

  logf("--- Processing burst frame %d ---", cap.id);

  size_t rgbLen = (size_t)cap.w * (size_t)cap.h * 3;
  uint8_t *rgb = (uint8_t *)heap_caps_malloc(rgbLen, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
  if (!rgb) {
    logLine("RGB decode buffer allocation failed");
    res.status = "RGB_ALLOC_FAIL";
    return false;
  }

  bool ok = fmt2rgb888(cap.jpg, cap.len, PIXFORMAT_JPEG, rgb);
  if (!ok) {
    logLine("fmt2rgb888 failed");
    free(rgb);
    res.status = "RGB_DECODE_FAIL";
    return false;
  }

  FomoBox fomoBox;
  bool fomoOk = runFomoFromRGB(rgb, cap.w, cap.h, fomoBox);
  CropRect crop;
  if (fomoOk) {
    crop = getFomoCrop(fomoBox, cap.w, cap.h);
    logf("Using FOMO crop: center=(%d,%d) conf=%.3f", fomoBox.fullCx, fomoBox.fullCy, fomoBox.conf);
  } else if (USE_FIXED_CROP_FALLBACK) {
    logLine("FOMO failed; using fixed crop fallback");
    crop = getFixedCrop(cap.w, cap.h);
  } else {
    logLine("FOMO failed; no fallback");
    free(rgb);
    res.status = "FOMO_FAIL";
    return false;
  }

#if USE_SD_DEBUG && SAVE_CROP_BMP
  char cropPath[40];
  snprintf(cropPath, sizeof(cropPath), "/crop_%04d.bmp", cap.id);
  saveBmpCropRGB888(cropPath, rgb, cap.w, cap.h, crop);
#endif

  if (!fillYoloInputFromRGB(rgb, cap.w, cap.h, crop)) {
    logLine("fillYoloInputFromRGB failed");
    free(rgb);
    res.status = "INPUT_FAIL";
    return false;
  }

#if USE_SD_DEBUG && SAVE_MODEL_INPUT_BMP
  char inputPath[44];
  snprintf(inputPath, sizeof(inputPath), "/yolo_input_%04d.bmp", cap.id);
  saveYoloInputBmp(inputPath);
#endif

  free(rgb);

  logf("Before Invoke frame %d: freeHeap=%u freePsram=%u", cap.id, ESP.getFreeHeap(), ESP.getFreePsram());
  uint32_t t0 = millis();
  TfLiteStatus invoke_status = interpreter->Invoke();
  uint32_t dt = millis() - t0;
  logf("Invoke frame %d status=%d time_ms=%u", cap.id, (int)invoke_status, (unsigned)dt);
  logf("After Invoke frame %d: freeHeap=%u freePsram=%u", cap.id, ESP.getFreeHeap(), ESP.getFreePsram());
  yield();
  delay(20);

  if (invoke_status != kTfLiteOk) {
    res.status = "INVOKE_FAIL";
    return false;
  }

  String reading;
  float avgConf = 0.0f;
  int detCount = 0;
  if (!decodeYolo(reading, avgConf, detCount)) {
    logLine("No YOLO detections for this frame");
    res.status = "NO_DIGITS";
    res.score = -1.0f;
    return false;
  }

  res.reading = reading;
  res.avgConf = avgConf;
  res.detCount = detCount;
  res.status = classifyStatus(reading, avgConf, detCount);
  res.score = qualityScore(reading, avgConf, detCount, res.status);
  res.ok = true;

  logf("FRAME %d reading=%s avgConf=%.3f detCount=%d status=%s score=%.3f",
       cap.id, res.reading.c_str(), res.avgConf, res.detCount, res.status.c_str(), res.score);
  return true;
}

static int chooseBestResult(FrameResult results[], int n) {
  int best = -1;

  // Consensus first: if same reading appears more than once, prefer it.
  for (int i = 0; i < n; i++) {
    if (!results[i].ok || results[i].reading.length() == 0) continue;
    int count = 1;
    float combined = results[i].score;
    for (int j = i + 1; j < n; j++) {
      if (results[j].ok && results[j].reading == results[i].reading) {
        count++;
        combined += results[j].score;
      }
    }
    if (count >= 2) {
      results[i].score = combined + 1.0f; // strong bonus for repeated exact match
      best = i;
      break;
    }
  }

  // Otherwise choose highest quality score.
  for (int i = 0; i < n; i++) {
    if (!results[i].ok) continue;
    if (best < 0 || results[i].score > results[best].score) best = i;
  }
  return best;
}

static void runOneCapture() {
  logLine("--- BURST FOMO-crop + YOLO workflow start ---");
  logf("LED=%s burstCount=%d", ledOn ? "ON" : "OFF", BURST_CAPTURE_COUNT);

  if (ledOn) delay(LED_STABILIZE_MS);
  sendMeterPacket("....", 0.0f, "PROCESSING");

  CaptureCopy caps[BURST_CAPTURE_COUNT];
  int got = 0;

  // Capture all images first before running the slow YOLO model.
  for (int i = 0; i < BURST_CAPTURE_COUNT; i++) {
    saveCounter++;
    if (captureJpegCopy(caps[got], saveCounter)) {
      got++;
    }
    delay(BURST_GAP_MS);
  }

  if (got == 0) {
    sendMeterPacket("----", 0.0f, "CAPTURE_FAIL");
    return;
  }

  logf("Burst capture complete: got=%d. Starting inference now.", got);

  FrameResult results[BURST_CAPTURE_COUNT];
  for (int i = 0; i < got; i++) {
    processCapturedJpeg(caps[i], results[i]);
    freeCapture(caps[i]);
  }

  int best = chooseBestResult(results, got);
  if (best < 0) {
    logLine("No valid result from burst");
    sendMeterPacket("----", 0.0f, "NO_DIGITS");
    return;
  }

  String finalStatus = results[best].status;
  // If we had multiple captures and no exact consensus, be honest in status.
  bool exactConsensus = false;
  for (int i = 0; i < got; i++) {
    if (i != best && results[i].ok && results[i].reading == results[best].reading) exactConsensus = true;
  }
  if (got >= 2 && !exactConsensus && finalStatus == "OK") finalStatus = "BEST_GUESS";

  logf("FINAL BURST reading=%s avgConf=%.3f detCount=%d status=%s score=%.3f fromFrame=%d",
       results[best].reading.c_str(), results[best].avgConf, results[best].detCount,
       finalStatus.c_str(), results[best].score, results[best].id);

  sendMeterPacket(results[best].reading, results[best].avgConf, finalStatus);
}

static void handleSerialCommands() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == 'c' || ch == 'C') {
      runOneCapture();
    } else if (ch == 'l' || ch == 'L') {
      setLed(!ledOn);
      logf("LED toggled by serial: %s", ledOn ? "ON" : "OFF");
    } else if (ch == 'm' || ch == 'M') {
      YOLO_USE_STRETCH = !YOLO_USE_STRETCH;
      logf("YOLO preprocess mode now: %s", YOLO_USE_STRETCH ? "STRETCH" : "LETTERBOX");
    } else if (ch == '+') {
      YOLO_CONF_THRESH += 0.05f;
      if (YOLO_CONF_THRESH > 0.95f) YOLO_CONF_THRESH = 0.95f;
      logf("YOLO_CONF_THRESH=%.2f", YOLO_CONF_THRESH);
    } else if (ch == '-') {
      YOLO_CONF_THRESH -= 0.05f;
      if (YOLO_CONF_THRESH < 0.01f) YOLO_CONF_THRESH = 0.01f;
      logf("YOLO_CONF_THRESH=%.2f", YOLO_CONF_THRESH);
    }
  }
}

static void handleButtons() {
#if USE_BUTTONS
  uint32_t now = millis();

  bool capState = digitalRead(CAPTURE_BUTTON_PIN);
  if (lastCaptureButtonState == HIGH && capState == LOW && now - lastCaptureButtonMs > 700) {
    lastCaptureButtonMs = now;
    runOneCapture();
  }
  lastCaptureButtonState = capState;

  bool ledState = digitalRead(LED_BUTTON_PIN);
  if (lastLedButtonState == HIGH && ledState == LOW && now - lastLedButtonMs > 300) {
    lastLedButtonMs = now;
    setLed(!ledOn);
    logf("LED toggled by button: %s", ledOn ? "ON" : "OFF");
  }
  lastLedButtonState = ledState;
#endif
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(1500);
  Serial.println();
  Serial.println("=== ESP32-CAM CHIRALE FOMO + CHIRALE YOLO + UART V2 INITFIX ===");

  setCpuFrequencyMhz(240);
  pinMode(FLASH_LED_PIN, OUTPUT);
  setLed(false);

#if USE_BUTTONS
  pinMode(CAPTURE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_BUTTON_PIN, INPUT_PULLUP);
#else
  logLine("Physical buttons enabled. Serial also works: c=capture, l=LED toggle.");
#endif

  logf("Free heap: %u", ESP.getFreeHeap());
  logf("Free PSRAM: %u", ESP.getFreePsram());
  logf("PSRAM found: %s", psramFound() ? "YES" : "NO");
  logf("FOMO model bytes: %u", (unsigned)fomo_model_tflite_len);
  logf("YOLO model bytes: %u", (unsigned)digit_model_tflite_len);

  initSD();

  if (!initCamera()) {
    sendMeterPacket("----", 0.0f, "CAM_INIT_FAIL");
    return;
  }

  if (!initFomoModel()) {
    sendMeterPacket("----", 0.0f, "FOMO_INIT_FAIL");
    return;
  }

  if (!initYoloModel()) {
    sendMeterPacket("----", 0.0f, "YOLO_INIT_FAIL");
    return;
  }

  logLine("Ready. Commands: c=capture, l=toggle LED, m=toggle preprocess, +=raise conf, -=lower conf");
  sendMeterPacket("BOOT", 1.0f, "READY");
}

void loop() {
  handleSerialCommands();
  handleButtons();
  delay(20);
}

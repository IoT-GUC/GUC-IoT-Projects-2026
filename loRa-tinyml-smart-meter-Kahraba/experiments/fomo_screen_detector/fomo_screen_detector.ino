#include <esp_camera.h>
#include <SD_MMC.h>
#include <smart-meter-screen-fomo_inferencing.h>

// ── Camera pins (AI-Thinker ESP32-CAM) ───────────────────────
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
#define BUTTON_PIN        13   // capture button
#define LED_BUTTON_PIN    12   // toggles LED ON/OFF manually (WARNING: GPIO2 is SD D0 on AI-Thinker)
#define FLASH_PIN          4   // onboard flash LED

static int counter = 0;

static bool ledEnabled = false;
static bool lastLedButtonReading = HIGH;
static bool stableLedButtonState = HIGH;
static unsigned long lastLedDebounceTime = 0;
const unsigned long LED_DEBOUNCE_MS = 50;

// ── SD log helper ─────────────────────────────────────────────
void logSD(const char *msg) {
    Serial.println(msg);
    File f = SD_MMC.open("/log.txt", FILE_APPEND);
    if (f) {
        f.println(msg);
        f.close();
    }
}

void logSDf(const char *fmt, ...) {
    char buf[128];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    logSD(buf);
}

// ── Camera init ───────────────────────────────────────────────
bool initCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size   = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count     = 1;
    config.fb_location  = CAMERA_FB_IN_PSRAM;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed: 0x%x\n", err);
        return false;
    }

    // improve image quality settings
    sensor_t *s = esp_camera_sensor_get();
    s->set_brightness(s, 0);     // brighter
    s->set_contrast(s, 1);       // more contrast
    s->set_saturation(s, -2);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_exposure_ctrl(s, 1);  // auto exposure on
    s->set_aec2(s, 1);
    s->set_gain_ctrl(s, 1);      // auto gain on
    s->set_vflip(s, 1);       // vertical flip
    s->set_hmirror(s, 0);     // horizontal mirror
    s->set_agc_gain(s, 5);
    // 0 = Normal, 1 = Negative, 2 = Grayscale, 3 = Red Tint...
    s->set_special_effect(s, 0); // Setting to 2 (Grayscale) clarifies OCR processing

    return true;
}

// ── Save file to SD ───────────────────────────────────────────
bool saveToSD(const char *path, uint8_t *buf, size_t len) {
    File f = SD_MMC.open(path, FILE_WRITE);
    if (!f) {
        logSDf("Failed to open %s", path);
        return false;
    }
    f.write(buf, len);
    f.close();
    return true;
}

// ── FOMO inference ────────────────────────────────────────────
bool runFOMO(camera_fb_t *fb,
             int *out_x, int *out_y,
             int *out_w, int *out_h)
{
    // allocate for full image decode
    size_t full_rgb_len = fb->width * fb->height * 3;
    uint8_t *full_rgb = (uint8_t*)ps_malloc(full_rgb_len);
    if (!full_rgb) {
        logSD("PSRAM alloc failed for full_rgb");
        return false;
    }

    bool ok = fmt2rgb888(fb->buf, fb->len, PIXFORMAT_JPEG, full_rgb);
    if (!ok) {
        logSD("JPEG decode failed");
        free(full_rgb);
        return false;
    }
    logSD("JPEG decoded OK");

    // allocate for resized EI input (96x96x3)
    size_t ei_rgb_len = EI_CLASSIFIER_INPUT_WIDTH *
                        EI_CLASSIFIER_INPUT_HEIGHT * 3;
    uint8_t *ei_rgb = (uint8_t*)ps_malloc(ei_rgb_len);
    if (!ei_rgb) {
        logSD("PSRAM alloc failed for ei_rgb");
        free(full_rgb);
        return false;
    }

    // nearest-neighbour resize to 96x96
    int src_w = fb->width;
    int src_h = fb->height;
    int dst_w = EI_CLASSIFIER_INPUT_WIDTH;
    int dst_h = EI_CLASSIFIER_INPUT_HEIGHT;

    for (int dy = 0; dy < dst_h; dy++) {
        for (int dx = 0; dx < dst_w; dx++) {
            int sx = dx * src_w / dst_w;
            int sy = dy * src_h / dst_h;
            size_t src_idx = (sy * src_w + sx) * 3;
            size_t dst_idx = (dy * dst_w + dx) * 3;
            ei_rgb[dst_idx]     = full_rgb[src_idx];
            ei_rgb[dst_idx + 1] = full_rgb[src_idx + 1];
            ei_rgb[dst_idx + 2] = full_rgb[src_idx + 2];
        }
    }
    free(full_rgb);
    logSD("Resize OK");

    // wrap in EI signal
    ei::signal_t signal;
    signal.total_length = dst_w * dst_h;

    uint8_t *_rgb = ei_rgb;
    signal.get_data = [_rgb](size_t offset, size_t length,
                              float *out_ptr) -> int {
        for (size_t i = 0; i < length; i++) {
            size_t idx = (offset + i) * 3;
            uint8_t r  = _rgb[idx];
            uint8_t g  = _rgb[idx + 1];
            uint8_t b  = _rgb[idx + 2];
            out_ptr[i] = (float)((r << 16) | (g << 8) | b);
        }
        return 0;
    };

    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR ei_err = run_classifier(&signal, &result, false);
    free(ei_rgb);

    if (ei_err != EI_IMPULSE_OK) {
        logSDf("Classifier error: %d", ei_err);
        return false;
    }

    logSDf("FOMO: %d detections", result.bounding_boxes_count);

    // log ALL detections regardless of threshold
    for (size_t i = 0; i < result.bounding_boxes_count; i++) {
        auto &bb = result.bounding_boxes[i];
        logSDf("  [%s] conf=%.2f x=%d y=%d w=%d h=%d",
               bb.label, bb.value,
               bb.x, bb.y, bb.width, bb.height);
    }

    // pick best detection above threshold
    float best_conf = 0.3f;   // lowered from 0.5
    bool  found     = false;

    for (size_t i = 0; i < result.bounding_boxes_count; i++) {
        auto &bb = result.bounding_boxes[i];
        if (bb.value > best_conf) {
            best_conf = bb.value;
            *out_x    = bb.x;
            *out_y    = bb.y;
            *out_w    = bb.width;
            *out_h    = bb.height;
            found     = true;
        }
    }

    if (!found) logSD("No detection above threshold");
    return found;
}


// ── Find next available image index ───────────────────────────
int getNextAvailableIndex() {
    int i = 0;

    while (true) {
        char full_path[32];
        char crop_path[32];

        sprintf(full_path, "/full_%04d.jpg", i);
        sprintf(crop_path, "/crop_%04d.txt", i);

        // If both names are free, use this index
        if (!SD_MMC.exists(full_path) && !SD_MMC.exists(crop_path)) {
            return i;
        }

        i++;

        // safety limit
        if (i > 9999) {
            return i;
        }
    }
}


// ── Manual LED button handler ─────────────────────────────────
// Press LED_BUTTON_PIN once to toggle the flash LED ON/OFF.
// The capture code will NOT flash automatically anymore.
void handleLedButton() {
    bool reading = digitalRead(LED_BUTTON_PIN);

    if (reading != lastLedButtonReading) {
        lastLedDebounceTime = millis();
        lastLedButtonReading = reading;
    }

    if ((millis() - lastLedDebounceTime) > LED_DEBOUNCE_MS) {
        if (reading != stableLedButtonState) {
            stableLedButtonState = reading;

            // button press: INPUT_PULLUP means pressed = LOW
            if (stableLedButtonState == LOW) {
                ledEnabled = !ledEnabled;
                digitalWrite(FLASH_PIN, ledEnabled ? HIGH : LOW);
                logSDf("LED manually toggled: %s", ledEnabled ? "ON" : "OFF");
            }
        }
    }
}

// ── Discard warm-up frames ────────────────────────────────────
// This lets auto exposure / auto gain settle before the real saved capture.
void discardWarmupFrames(int count) {
    logSDf("Discarding %d warm-up frames...", count);

    for (int i = 0; i < count; i++) {
        camera_fb_t *warm = esp_camera_fb_get();

        if (warm) {
            logSDf("  Warm-up frame %d: %dx%d %d bytes",
                   i + 1, warm->width, warm->height, warm->len);
            esp_camera_fb_return(warm);
        } else {
            logSDf("  Warm-up frame %d failed", i + 1);
        }

        delay(100);
    }

    logSD("Warm-up done");
}


// ── Setup ─────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(LED_BUTTON_PIN, INPUT_PULLUP);
    pinMode(FLASH_PIN,  OUTPUT);
    digitalWrite(FLASH_PIN, LOW);

    if (psramFound())
        Serial.printf("PSRAM: %d bytes\n", ESP.getPsramSize());
    else
        Serial.println("WARNING: No PSRAM");

    if (!initCamera()) {
        Serial.println("Camera failed — halting");
        while (true) delay(1000);
    }
    Serial.println("Camera OK");

    if (!SD_MMC.begin("/sdcard", true)) {
        Serial.println("SD failed — halting");
        while (true) delay(1000);
    }

    if (SD_MMC.cardType() == CARD_NONE) {
        Serial.println("No SD card");
        while (true) delay(1000);
    }

    Serial.printf("SD OK — %.0f MB\n",
                  (float)SD_MMC.cardSize() / (1024 * 1024));


    // clear old log
    SD_MMC.remove("/log.txt");
    logSD("=== Boot OK ===");
    counter = getNextAvailableIndex();
    logSDf("Starting counter at: %d", counter);
    logSD("Ready. Press capture button. Press GPIO2 button to toggle LED.");
}

// ── Loop ──────────────────────────────────────────────────────
void loop() {
    // Check LED toggle button all the time
    handleLedButton();

    if (digitalRead(BUTTON_PIN) != LOW)
        return;

    delay(50);
    if (digitalRead(BUTTON_PIN) != LOW)
        return;

    logSD("\n── Capturing ──");
    logSDf("LED state during capture: %s", ledEnabled ? "ON" : "OFF");

    // No automatic flash here.
    // LED stays exactly as manually selected by LED_BUTTON_PIN.
    discardWarmupFrames(3);

    camera_fb_t *fb = esp_camera_fb_get();

    if (!fb) {
        logSD("Capture failed");
        return;
    }

    logSDf("Captured: %dx%d  %d bytes",
           fb->width, fb->height, fb->len);

    // save full image
    char full_path[32];
    sprintf(full_path, "/full_%04d.jpg", counter);
    if (saveToSD(full_path, fb->buf, fb->len))
        logSDf("Saved: %s", full_path);

    // run FOMO
    int bx, by, bw, bh;
    bool found = runFOMO(fb, &bx, &by, &bw, &bh);

    if (found) {
        logSDf("Screen at: x=%d y=%d w=%d h=%d", bx, by, bw, bh);

        char coord_path[32];
        sprintf(coord_path, "/crop_%04d.txt", counter);
        char coord_str[64];
        sprintf(coord_str, "%d,%d,%d,%d\n", bx, by, bw, bh);
        if (saveToSD(coord_path,
                     (uint8_t*)coord_str, strlen(coord_str)))
            logSDf("Coords saved: %s", coord_path);
    } else {
        logSD("No screen detected");
    }

    esp_camera_fb_return(fb);
    counter++;
    logSDf("Done. Counter: %d", counter);

    while (digitalRead(BUTTON_PIN) == LOW) delay(10);
    delay(300);
}
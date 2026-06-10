#include "esp_camera.h"
#include "FS.h"
#include "SD_MMC.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// -----------------------------
// CAMERA PINS (AI Thinker)
// -----------------------------
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

// -----------------------------
// BUTTON PIN
// -----------------------------
#define BUTTON_PIN 13
#define LED_BUTTON_PIN 12
#define FLASH_LED_PIN 4
bool ledState = false;

int imageCount = 0;

void setup() {

  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  Serial.println();

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_BUTTON_PIN, INPUT_PULLUP);

  pinMode(FLASH_LED_PIN, OUTPUT);

  digitalWrite(FLASH_LED_PIN, LOW);

  // -----------------------------
  // Camera Config
  // -----------------------------
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

  // -----------------------------
  // IMPORTANT SETTINGS
  // -----------------------------

  config.pixel_format = PIXFORMAT_JPEG;

  // Use QVGA = 320x240
  // VGA = 640x480
  config.frame_size = FRAMESIZE_VGA;

  // Lower number = better quality
  // 10-15 is good
  config.jpeg_quality = 10;

  config.fb_count = 1;

  // -----------------------------
  // Init Camera
  // -----------------------------

  esp_err_t err = esp_camera_init(&config);


  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return;
  }
  sensor_t * s = esp_camera_sensor_get();

  s->set_vflip(s, 1);       // vertical flip
  s->set_hmirror(s, 0);     // horizontal mirror

  Serial.println("Camera initialized.");

  // -----------------------------
  // Init SD Card
  // -----------------------------

if (!SD_MMC.begin("/sdcard", true)) {
  Serial.println("SD Card Mount Failed");
  return;
}

  uint64_t cardSize = SD_MMC.cardSize() / (1024 * 1024);

  Serial.printf("SD Card Size: %lluMB\n", cardSize);
  //imageCount = getNextImageIndex();
  Serial.printf("Starting from image index: %d\n", imageCount);

  Serial.println("Ready to capture images.");
  Serial.println("Press button to capture.");
}

void loop() {
  if (digitalRead(LED_BUTTON_PIN) == LOW) {

  delay(200);

  ledState = !ledState;

  digitalWrite(FLASH_LED_PIN, ledState);

  if (ledState) {
    Serial.println("LED ON");
  } else {
    Serial.println("LED OFF");
  }

  while (digitalRead(LED_BUTTON_PIN) == LOW) {
    delay(10);
    }
  }

  // Button pressed
  if (digitalRead(BUTTON_PIN) == LOW) {

    delay(200);

    captureImage();

    // Wait until button released
    while (digitalRead(BUTTON_PIN) == LOW) {
      delay(10);
    }
  }
}

void captureImage() {

  Serial.println("Capturing image...");

  camera_fb_t * fb = esp_camera_fb_get();

  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  imageCount = getNextImageIndex();

  String path = "/meter_" + String(imageCount) + ".jpg";

  File file = SD_MMC.open(path.c_str(), FILE_WRITE);

  if (!file) {
    Serial.println("Failed to open file");
  }
  else {

    file.write(fb->buf, fb->len);

    Serial.printf("Saved: %s\n", path.c_str());

    file.close();

    imageCount++;
  }

  esp_camera_fb_return(fb);

  delay(500);
}
int getNextImageIndex() {
  int index = imageCount;

  while (true) {
    String path = "/meter_" + String(index) + ".jpg";

    if (!SD_MMC.exists(path)) {
      return index;  // found unused filename
    }

    index++;
  }
}
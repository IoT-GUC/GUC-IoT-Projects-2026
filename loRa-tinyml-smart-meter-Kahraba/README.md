# Kaharaba - TinyML Smart Meter

## Project Description
This project implements an embedded IoT system for automatically reading electricity meter LCD values using an ESP32-CAM and transmitting the reading wirelessly using LoRa.

## Team
Team Name: Kharaba
Members:
- Kareem
- Youssef
- Youssef
- Adham
- Omar

## System Architecture
1) ESP32-CAM captures meter image 
2) A burst capture is done taking multiple pictures
3) FOMO detects LCD screen
4) LCD crop is processed using classical CV resulting in a dynamic crop
5) Digits are classified using micro YOLO model
6) Reading is sent through UART 
7) LilyGo device transmits/receives via LoRa
8) Results are shown on the dashboard


## Technologies Used
- ESP32-CAM
- LilyGo T-Display
- LoRa
- Edge Impulse FOMO
- TensorFlow Lite Micro
- OpenCV / Python
- Arduino IDE / PlatformIO
- YOLO 

## Implementation Details
### Screen Detection
FOMO model detects the LCD screen region.

### Digit Segmentation
Classical computer vision is used to segment digits from the detected LCD crop.

### Digit Classification
A lightweight YOLO model classifies each digit crop.

### Communication
UART is used between ESP32-CAM and LilyGo. LoRa is used for long-range wireless transmission. 
A MQTT is used to send data to the dashboard.

## Progress Achieved
- Screen detection using FOMO works on ESP32-CAM.
- Digit classifier trained and quantized.
- Python segmentation pipeline tested.
- UART/LoRa communication prototype prepared.
- Camera capture and SD saving tested.
- Several model alternatives evaluated.

## Current Limitations
- Digit segmentation is still sensitive to lighting and seven-segment digit splitting.
- Some digit pairs may be confused, such as 2/5, 0/8, and 3/9.

## Design Decisions
- FOMO was selected for lightweight screen detection.
- INT8 quantization was used to reduce model size.


# Medical Clinic Digital Twin (Central Link)

## Overview
The **Medical Clinic Digital Twin** is an IoT-based smart healthcare monitoring system designed to optimize patient flow management within clinics and hospitals. By addressing "operational blindness"—the lack of real-time visibility into patient movement—our system automates patient tracking to identify bottlenecks, reduce waiting times, and improve staff allocation.

## Problem Statement
Traditional patient tracking methods rely on manual check-ins, leading to:
- Overcrowded waiting rooms.
- Inefficient staff utilization.
- Fragmented patient movement data.
- Poor overall patient experience.

Our solution creates a real-time digital twin using Bluetooth Low Energy (BLE) tags to provide administrators with actionable, data-driven insights.

## System Architecture
The system follows a tiered IoT architecture:
1.  **Perception Layer (End Devices):** BLE wearable tags assigned to patients, broadcasting unique IDs.
2.  **Edge Layer (Gateways):** ESP32 gateway nodes installed at strategic zones (Reception, Waiting Area, Examination Rooms, Pharmacy) to capture BLE signals and calculate RSSI.
3.  **Network Layer:** Wi-Fi/Ethernet connectivity using MQTT over TLS for secure data transmission.
4.  **Processing Layer (Cloud):** Node.js backend running on an Ubuntu VM, handling data reconciliation (RSSI/timestamp), database storage, and ML-based anomaly detection.
5.  **Application Layer:** Web dashboard visualizing live patient locations, heatmaps, and workflow analytics.

## Key Features
- **Real-Time Visualization:** Live map displaying patient movements across the clinic.
- **Workflow Analytics:** Automated calculation of stay durations, peak hours, and department efficiency.
- **Anomaly Detection:** ML-powered alerts for unexpected patient loops, long waits, or crowded zones.
- **Secure Communication:** HIPAA-grade privacy using MQTTS (TLS 1.2/1.3).

## API Documentation
The system exposes a RESTful API for managing hospitals, routers, devices, and tracking records. Key endpoints include:
- `POST /auth/signup`: Hospital registration.
- `GET /routers/map`: Real-time location and occupancy overview.
- `GET /patients/{id}/sessions`: Detailed session history per patient.
- `GET /records/hourly-patients`: Analytics for unique hourly patient counts.

*(For detailed specifications, see `clinic-iot-init/endpoints.json`)*

## Deployment & Setup
The project is hosted on an Ubuntu-based cloud VM. Deployment steps include:

1.  **Server Setup:** Configure Ubuntu VM and install essential packages (curl, git, net-tools, ufw).
2.  **Broker Setup:** Install and secure **Mosquitto MQTT** with TLS (Port 8883).
3.  **Backend:** Deploy the Node.js backend using `pm2` for process management.
4.  **Frontend:** Run the Gunicorn-served application and configure Nginx as a reverse proxy.
5.  **SSL:** Use Certbot for Let's Encrypt certificates to secure the web dashboard.

*(Refer to `clinic-iot-deployment/VM Config.md` for detailed commands and configuration snippets)*

## Project Team
- **Central Link Team**
- **Supervisor:** Prof. Tallal El-Shabrawy
- **Members:** Khalid Ashmawy, Ahmed Khedr, Abdallah Mohamed, Abdullah Sherif, Ahmed Farag

---
*Developed for the IoT Elective, 2026.*
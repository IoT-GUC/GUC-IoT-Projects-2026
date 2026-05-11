import serial
import requests
import json
from datetime import datetime, timezone

SERIAL_PORT = "COM3"   # change if your receiver is on another port
BAUD_RATE = 115200

FIREBASE_DB_URL = "https://outdoor-asset-localization-default-rtdb.firebaseio.com"

def firebase_put(path: str, data: dict) -> None:
    url = f"{FIREBASE_DB_URL}/{path}.json"
    response = requests.put(url, json=data, timeout=10)
    response.raise_for_status()

def firebase_post(path: str, data: dict) -> None:
    url = f"{FIREBASE_DB_URL}/{path}.json"
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def parse_packet_block(lines):
    data = {}

    for line in lines:
        line = line.strip()

        if line.startswith("ID:"):
            data["deviceId"] = line.replace("ID:", "", 1).strip()
        elif line.startswith("Fix:"):
            value = line.replace("Fix:", "", 1).strip()
            data["fix"] = int(value) if value.isdigit() else 0
        elif line.startswith("Lat:"):
            value = line.replace("Lat:", "", 1).strip()
            data["latitude"] = float(value) if value not in ["NA", ""] else None
        elif line.startswith("Lng:"):
            value = line.replace("Lng:", "", 1).strip()
            data["longitude"] = float(value) if value not in ["NA", ""] else None
        elif line.startswith("UTC:"):
            data["timestampUtc"] = line.replace("UTC:", "", 1).strip()
        elif line.startswith("Sats:"):
            value = line.replace("Sats:", "", 1).strip()
            data["satellites"] = int(value) if value.isdigit() else 0
        elif line.startswith("HDOP:"):
            value = line.replace("HDOP:", "", 1).strip()
            try:
                data["hdop"] = float(value)
            except ValueError:
                data["hdop"] = None
        elif line.startswith("Uptime:"):
            value = line.replace("Uptime:", "", 1).strip()
            data["uptime"] = int(value) if value.isdigit() else 0
        elif line.startswith("RSSI:"):
            value = line.replace("RSSI:", "", 1).strip()
            try:
                data["rssi"] = int(value)
            except ValueError:
                data["rssi"] = None

    if "deviceId" not in data:
        return None

    data["receivedAt"] = now_utc_iso()
    return data

def save_to_firebase(record):
    device_id = record["deviceId"]
    firebase_put(f"assets/{device_id}/latest", record)
    firebase_post(f"assets/{device_id}/history", record)

def main():
    print(f"Opening serial port {SERIAL_PORT} at {BAUD_RATE} baud...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    packet_lines = []
    inside_packet = False

    print("Listening for receiver packets...")

    while True:
        raw_line = ser.readline().decode(errors="ignore").strip()
        if not raw_line:
            continue

        print(raw_line)

        if raw_line == "----- PACKET -----":
            packet_lines = []
            inside_packet = True
            continue

        if raw_line == "------------------" and inside_packet:
            inside_packet = False
            record = parse_packet_block(packet_lines)

            if record is None:
                print("Could not parse packet block.")
                continue

            try:
                save_to_firebase(record)
                print("Saved to Firebase:", json.dumps(record, indent=2))
            except Exception as e:
                print("Firebase upload failed:", str(e))

            continue

        if inside_packet:
            packet_lines.append(raw_line)

if __name__ == "__main__":
    main()



#python serial_to_firebase.py
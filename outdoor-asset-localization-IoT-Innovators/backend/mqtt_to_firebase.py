import json
import os
from datetime import datetime, timezone
from urllib.parse import quote

import requests
import paho.mqtt.client as mqtt


# =======================================================
# Configuration
# =======================================================

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

MQTT_TOPIC_ALL = os.getenv("MQTT_TOPIC_ALL", "iot-innovators/assets/all")

MQTT_CLIENT_ID = os.getenv(
    "MQTT_CLIENT_ID",
    "iot-innovators-mqtt-to-firebase-bridge"
)

FIREBASE_BASE_URL = os.getenv(
    "FIREBASE_BASE_URL",
    "https://outdoor-asset-localization-default-rtdb.firebaseio.com"
)

REQUEST_TIMEOUT_SECONDS = 10


# =======================================================
# Helper Functions
# =======================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def firebase_url(path: str) -> str:
    clean_base = FIREBASE_BASE_URL.rstrip("/")
    clean_path = path.strip("/")
    return f"{clean_base}/{clean_path}.json"


def safe_device_id(device_id: str) -> str:
    return quote(str(device_id), safe="")


def validate_location_record(record: dict) -> tuple[bool, str]:
    required_fields = [
        "deviceID",
        "fix",
        "latitude",
        "longitude",
        "timestamp_utc",
        "satellites",
        "hdop",
        "uptime",
        "rssi",
    ]

    for field in required_fields:
        if field not in record:
            return False, f"Missing required field: {field}"

    try:
        float(record["latitude"])
        float(record["longitude"])
        int(record["fix"])
        int(record["satellites"])
        float(record["hdop"])
        int(record["uptime"])
        int(record["rssi"])
    except ValueError as exc:
        return False, f"Invalid numeric value: {exc}"
    except TypeError as exc:
        return False, f"Invalid field type: {exc}"

    return True, "valid"


def normalize_record(record: dict) -> dict:
    """
    Normalize MQTT JSON into the Firebase structure.

    This stores both:
    1. Main MQTT/Firebase field names.
    2. Dashboard-compatible aliases used by dashboard_v1.html.

    This avoids N/A values in the dashboard when the old dashboard expects
    slightly different field names.
    """

    now = utc_now_iso()

    device_id = str(record["deviceID"])
    timestamp_utc = str(record["timestamp_utc"])

    latitude = float(record["latitude"])
    longitude = float(record["longitude"])
    fix = int(record["fix"])
    satellites = int(record["satellites"])
    hdop = float(record["hdop"])
    uptime = int(record["uptime"])
    rssi = int(record["rssi"])

    normalized = {
        # =======================================================
        # Main MQTT/Firebase fields
        # =======================================================
        "deviceID": device_id,
        "fix": fix,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp_utc": timestamp_utc,
        "satellites": satellites,
        "hdop": hdop,
        "uptime": uptime,
        "rssi": rssi,
        "gateway": str(record.get("gateway", "receiver01")),
        "packet_count": int(record.get("packet_count", 0)),
        "raw_payload": str(record.get("raw_payload", "")),
        "updated_at": now,
        "source": "mqtt",

        # =======================================================
        # Device ID aliases
        # =======================================================
        "device_id": device_id,
        "deviceId": device_id,
        "id": device_id,

        # =======================================================
        # UTC timestamp aliases
        # =======================================================
        "timestamp": timestamp_utc,
        "timestampUTC": timestamp_utc,
        "timestampUtc": timestamp_utc,
        "utc_timestamp": timestamp_utc,
        "utcTimestamp": timestamp_utc,
        "utc_time": timestamp_utc,
        "utcTime": timestamp_utc,
        "gps_time": timestamp_utc,
        "gpsTime": timestamp_utc,
        "time": timestamp_utc,

        # =======================================================
        # Received/update time aliases
        # =======================================================
        "received_at": now,
        "receivedAt": now,
        "last_updated": now,
        "lastUpdated": now,

        # =======================================================
        # Coordinate aliases
        # =======================================================
        "lat": latitude,
        "lng": longitude,

        # =======================================================
        # GPS fix aliases
        # =======================================================
        "gps_fix": fix,
        "gpsFix": fix,
        "valid_fix": fix == 1,
        "validFix": fix == 1,

        # =======================================================
        # Satellite/RSSI aliases
        # =======================================================
        "satellite_count": satellites,
        "satelliteCount": satellites,
        "signal_rssi": rssi,
        "signalRssi": rssi,
    }

    return normalized


def upload_to_firebase(record: dict) -> None:
    device_id = safe_device_id(record["deviceID"])

    latest_path = f"assets/{device_id}/latest"
    history_path = f"assets/{device_id}/history"

    latest_response = requests.put(
        firebase_url(latest_path),
        json=record,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    latest_response.raise_for_status()

    history_response = requests.post(
        firebase_url(history_path),
        json=record,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    history_response.raise_for_status()

    print("Uploaded to Firebase successfully.")
    print(f"Latest path: {latest_path}")
    print(f"History path: {history_path}")


# =======================================================
# MQTT Callbacks
# =======================================================

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected to MQTT broker.")
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Connection result: {reason_code}")

    client.subscribe(MQTT_TOPIC_ALL)
    print(f"Subscribed to topic: {MQTT_TOPIC_ALL}")


def on_disconnect(client, userdata, reason_code, properties=None):
    print("Disconnected from MQTT broker.")
    print(f"Reason: {reason_code}")


def on_message(client, userdata, message):
    print()
    print("========== MQTT Message Received ==========")
    print(f"Topic: {message.topic}")

    try:
        payload_text = message.payload.decode("utf-8")
        print(f"Payload: {payload_text}")

        record = json.loads(payload_text)

        is_valid, validation_message = validate_location_record(record)

        if not is_valid:
            print(f"Invalid record. Reason: {validation_message}")
            print("===========================================")
            return

        normalized_record = normalize_record(record)

        print("Normalized record:")
        print(json.dumps(normalized_record, indent=2))

        upload_to_firebase(normalized_record)

    except json.JSONDecodeError as exc:
        print(f"JSON decode error: {exc}")

    except requests.RequestException as exc:
        print(f"Firebase request error: {exc}")

    except Exception as exc:
        print(f"Unexpected error: {exc}")

    print("===========================================")


# =======================================================
# Main Program
# =======================================================

def create_mqtt_client():
    """
    Supports both newer and older paho-mqtt versions.
    """

    try:
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=MQTT_CLIENT_ID,
        )
    except AttributeError:
        client = mqtt.Client(client_id=MQTT_CLIENT_ID)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    return client


def main():
    print("===========================================")
    print("IoT Innovators MQTT to Firebase Bridge")
    print("Mode: MQTT Broker -> Firebase Realtime DB")
    print("===========================================")
    print(f"MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"MQTT topic: {MQTT_TOPIC_ALL}")
    print(f"Firebase URL: {FIREBASE_BASE_URL}")
    print()

    client = create_mqtt_client()

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    print("Waiting for MQTT messages...")
    client.loop_forever()


if __name__ == "__main__":
    main()
"""
MQTT Backend — writes incoming meter readings to meter_data.json
----------------------------------------------------------------
Run this separately from the dashboard:
    python backend.py
"""

import json
import os
from datetime import datetime
from paho.mqtt.enums import CallbackAPIVersion
import paho.mqtt.client as mqtt

# ── Configuration ────────────────────────────────────────────────
BROKER_IP   = "localhost"
BROKER_PORT = 1883
TOPIC       = "meters/+/data"
DATA_FILE   = "meter_data.json"
MAX_POINTS  = 100

# ── File storage ─────────────────────────────────────────────────
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def append_reading(topic, payload):
    parts = topic.split("/")
    device_id = parts[1] if len(parts) >= 3 else "unknown"

    data = load_data()
    if device_id not in data:
        data[device_id] = []

    payload["timestamp"] = datetime.now().strftime("%H:%M:%S")
    data[device_id].append(payload)

    if len(data[device_id]) > MAX_POINTS:
        data[device_id] = data[device_id][-MAX_POINTS:]

    save_data(data)
    print(f"✓ [{payload['timestamp']}] {topic} → {payload}")

# ── MQTT Callbacks ────────────────────────────────────────────────
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(TOPIC)
        print(f"✓ Connected to broker {BROKER_IP}:{BROKER_PORT}")
        print(f"  Subscribed to: {TOPIC}\n")
    else:
        print(f"✗ Connection failed (rc={reason_code})")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        append_reading(msg.topic, payload)
    except Exception as e:
        print(f"✗ Error processing message: {e}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print(f"⚠ Disconnected (rc={reason_code}), reconnecting...")

# ── Main ─────────────────────────────────────────────────────────
client = mqtt.Client(
    client_id="meter-backend",
    callback_api_version=CallbackAPIVersion.VERSION2
)
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect
client.reconnect_delay_set(min_delay=1, max_delay=10)

print(f"Connecting to {BROKER_IP}:{BROKER_PORT} ...")
client.connect(BROKER_IP, BROKER_PORT, keepalive=60)
client.loop_forever()

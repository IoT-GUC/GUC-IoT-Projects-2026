"""
Indoor Asset Localization — FastAPI Backend
Week 3: asset status, battery field, single-floor zones, no ThingsBoard
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import time
from datetime import datetime
from contextlib import contextmanager

app = FastAPI(title="Indoor Asset Localization API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "assets.db"

# ---------------------------------------------------------------------------
# Zone thresholds  — single floor only (TA requirement)
# Stored as a list so PUT /thresholds can hot-update them at runtime.
# ---------------------------------------------------------------------------
ZONE_THRESHOLDS = [
    (-60,  "Same Room"),
    (-80,  "Nearby Room"),
    (-100, "Same Floor"),   # furthest zone — still same physical floor
]

def get_zone(rssi: int) -> str:
    for threshold, zone in ZONE_THRESHOLDS:
        if rssi >= threshold:
            return zone
    return "Out of Range"

# ---------------------------------------------------------------------------
# Asset status logic
#   • "Active"       — last packet < 15 s ago
#   • "Idle"         — last packet 15–60 s ago
#   • "Out of Range" — last packet > 60 s ago
# ---------------------------------------------------------------------------
ACTIVE_SECS   = 15
IDLE_SECS     = 60

def get_status(received_at: int) -> str:
    age = int(time.time()) - received_at
    if age < ACTIVE_SECS:
        return "Active"
    if age < IDLE_SECS:
        return "Idle"
    return "Out of Range"

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        # Create table if it doesn't exist yet
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id    TEXT    NOT NULL,
                rssi        INTEGER NOT NULL,
                snr         REAL,
                battery     REAL,
                zone        TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL,
                received_at INTEGER NOT NULL
            )
        """)
        # Migrate existing DBs that pre-date the battery column
        existing = {row[1] for row in conn.execute("PRAGMA table_info(readings)")}
        if "battery" not in existing:
            conn.execute("ALTER TABLE readings ADD COLUMN battery REAL")
            print("[DB] Migrated: added 'battery' column to existing readings table")
        conn.commit()

init_db()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class TelemetryIn(BaseModel):
    assetID:   str
    rssi:      int
    snr:       Optional[float] = None
    battery:   Optional[float] = None
    timestamp: Optional[str]   = None

class ZoneThresholdUpdate(BaseModel):
    same_room:   int = -60
    nearby_room: int = -80
    same_floor:  int = -100

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/telemetry", summary="Receive a reading from the ESP32 receiver")
def post_telemetry(data: TelemetryIn):
    zone = get_zone(data.rssi)
    ts   = data.timestamp or datetime.utcnow().strftime("%H:%M:%S")
    now  = int(time.time())
    with get_db() as conn:
        conn.execute(
            """INSERT INTO readings
               (asset_id, rssi, snr, battery, zone, timestamp, received_at)
               VALUES (?,?,?,?,?,?,?)""",
            (data.assetID, data.rssi, data.snr, data.battery, zone, ts, now)
        )
        conn.commit()
    return {"status": "ok", "zone": zone}


@app.get("/assets", summary="List all known asset IDs")
def get_assets():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT asset_id FROM readings ORDER BY asset_id"
        ).fetchall()
    return {"assets": [r["asset_id"] for r in rows]}


@app.get("/assets/{asset_id}/latest", summary="Latest reading for one asset")
def get_latest(asset_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM readings WHERE asset_id=? ORDER BY received_at DESC LIMIT 1",
            (asset_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Asset not found")
    d = dict(row)
    d["status"] = get_status(d["received_at"])
    return d


@app.get("/assets/{asset_id}/history", summary="Recent N readings for one asset")
def get_history(asset_id: str, limit: int = 40):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM readings WHERE asset_id=? ORDER BY received_at DESC LIMIT ?",
            (asset_id, limit)
        ).fetchall()
    return {"history": [dict(r) for r in rows]}


@app.get("/overview", summary="Latest reading for every asset (with status)")
def get_overview():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT r.*
            FROM readings r
            INNER JOIN (
                SELECT asset_id, MAX(received_at) AS max_ts
                FROM readings GROUP BY asset_id
            ) latest ON r.asset_id = latest.asset_id
                     AND r.received_at = latest.max_ts
            ORDER BY r.asset_id
        """).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["status"] = get_status(d["received_at"])
        result.append(d)
    return {"assets": result}


@app.get("/stats", summary="Summary statistics per asset")
def get_stats():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                asset_id,
                COUNT(*)            AS total_packets,
                ROUND(AVG(rssi),1)  AS avg_rssi,
                MAX(rssi)           AS best_rssi,
                MIN(rssi)           AS worst_rssi,
                ROUND(AVG(snr),1)   AS avg_snr,
                ROUND(AVG(battery),2) AS avg_battery,
                MAX(received_at)    AS last_seen
            FROM readings
            GROUP BY asset_id
        """).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["last_seen_human"] = datetime.fromtimestamp(d["last_seen"]).strftime("%H:%M:%S")
        d["status"]          = get_status(d["last_seen"])
        result.append(d)
    return {"stats": result}


@app.get("/thresholds", summary="Get current RSSI zone thresholds")
def get_thresholds():
    return {
        "same_room":   ZONE_THRESHOLDS[0][0],
        "nearby_room": ZONE_THRESHOLDS[1][0],
        "same_floor":  ZONE_THRESHOLDS[2][0],
    }


@app.put("/thresholds", summary="Update RSSI zone thresholds at runtime")
def update_thresholds(body: ZoneThresholdUpdate):
    global ZONE_THRESHOLDS
    ZONE_THRESHOLDS = [
        (body.same_room,   "Same Room"),
        (body.nearby_room, "Nearby Room"),
        (body.same_floor,  "Same Floor"),
    ]
    return {"status": "updated", "thresholds": body.dict()}


@app.delete("/assets/{asset_id}", summary="Clear all readings for an asset")
def delete_asset(asset_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM readings WHERE asset_id=?", (asset_id,))
        conn.commit()
    return {"status": "deleted", "asset_id": asset_id}


@app.get("/health")
def health():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"]
    return {
        "status": "ok",
        "time":   datetime.utcnow().isoformat(),
        "total_readings": total,
    }
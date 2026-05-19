import base64
import json as _json
import time
import requests
import dotenv
import os


dotenv.load_dotenv()

BASE_URL = (os.getenv("API_BASE_URL") or "").strip()
TIMEOUT  = int(os.getenv("API_TIMEOUT", 10))
_token: str | None = None


def set_token(token: str | None):
    global _token
    _token = token


def token_is_valid() -> bool:
    """Decode JWT exp field (no signature check) to see if token is still live."""
    token = _token
    if not token:
        try:
            import flask
            token = flask.session.get("token")
        except Exception:
            pass
    if not token:
        return False
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
        return time.time() < payload.get("exp", 0)
    except Exception:
        return True  # can't decode — assume valid


def _auth() -> dict:
    token = _token
    if not token:
        # Fall back to Flask session if module-level token not set
        try:
            import flask
            token = flask.session.get("token")
        except Exception:
            pass
    return {"Authorization": f"Bearer {token}"} if token else {}


def _get(path: str) -> dict | None:
    try:
        r = requests.get(f"{BASE_URL}{path}", headers=_auth(), timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _post(path: str, json: dict) -> dict | None:
    try:
        r = requests.post(f"{BASE_URL}{path}", json=json, headers=_auth(), timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _post_verbose(path: str, json: dict) -> tuple[dict | None, str | None]:
    """Returns (data, error_message). error_message is None on success."""
    try:
        r = requests.post(f"{BASE_URL}{path}", json=json, headers=_auth(), timeout=TIMEOUT)
        if not r.ok:
            try:
                body = r.json()
                msg = body.get("message") or body.get("error") or f"HTTP {r.status_code}"
            except Exception:
                msg = f"HTTP {r.status_code}"
            return None, msg
        return r.json(), None
    except requests.exceptions.Timeout:
        return None, "Request timed out — is the server reachable?"
    except Exception as e:
        return None, str(e)


def _public_post_verbose(path: str, json: dict) -> tuple[dict | None, str | None]:
    """Same as _post_verbose but without auth headers (for /auth/* endpoints)."""
    try:
        r = requests.post(f"{BASE_URL}{path}", json=json, timeout=TIMEOUT)
        if not r.ok:
            try:
                body = r.json()
                msg = body.get("message") or body.get("error") or f"HTTP {r.status_code}"
            except Exception:
                msg = f"HTTP {r.status_code}"
            return None, msg
        return r.json(), None
    except requests.exceptions.Timeout:
        return None, "Request timed out — is the server reachable?"
    except Exception as e:
        return None, str(e)


def _patch_verbose(path: str, json: dict) -> tuple[dict | None, str | None]:
    """Returns (data, error_message). error_message is None on success."""
    try:
        r = requests.patch(f"{BASE_URL}{path}", json=json, headers=_auth(), timeout=TIMEOUT)
        if not r.ok:
            try:
                body = r.json()
                msg = body.get("message") or body.get("error") or f"HTTP {r.status_code}"
            except Exception:
                msg = f"HTTP {r.status_code}"
            return None, msg
        return r.json(), None
    except requests.exceptions.Timeout:
        return None, "Request timed out — is the server reachable?"
    except Exception as e:
        return None, str(e)


def _put_verbose(path: str, json: dict | None = None) -> tuple[dict | None, str | None]:
    """Returns (data, error_message). error_message is None on success."""
    try:
        r = requests.put(f"{BASE_URL}{path}", json=json, headers=_auth(), timeout=TIMEOUT)
        if not r.ok:
            try:
                body = r.json()
                msg = body.get("message") or body.get("error") or f"HTTP {r.status_code}"
            except Exception:
                msg = f"HTTP {r.status_code}"
            return None, msg
        return r.json(), None
    except requests.exceptions.Timeout:
        return None, "Request timed out — is the server reachable?"
    except Exception as e:
        return None, str(e)


def _put(path: str, json: dict | None = None) -> dict | None:
    try:
        r = requests.put(f"{BASE_URL}{path}", json=json, headers=_auth(), timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _delete(path: str, json: dict | None = None) -> bool:
    try:
        r = requests.delete(f"{BASE_URL}{path}", json=json, headers=_auth(), timeout=TIMEOUT)
        r.raise_for_status()
        return True
    except Exception:
        return False


# ── Auth ──────────────────────────────────────────────────────────────────────
def login(hospital_id: str, password: str) -> tuple[dict | None, str | None]:
    return _public_post_verbose("/auth/login",
                                {"hospital_id": hospital_id, "password": password})


def signup(hospital_id: str, name: str, address: str,
           admin_name: str, admin_email: str, password: str) -> tuple[dict | None, str | None]:
    return _public_post_verbose("/auth/signup",
                                {"hospital_id": hospital_id, "name": name,
                                 "address": address, "admin_name": admin_name,
                                 "admin_email": admin_email, "password": password})


# ── Routers ───────────────────────────────────────────────────────────────────
def get_routers() -> list:
    data = _get("/routers")
    return data.get("routers", []) if data else []


def get_routers_map() -> list:
    data = _get("/routers/map")
    return data.get("routers_map", []) if data else []


def get_active_routers() -> list:
    data = _get("/routers/active")
    return data.get("routers", []) if data else []


def get_router(router_id: str) -> dict | None:
    data = _get(f"/routers/{router_id}")
    return data.get("router") if data else None


def get_router_devices(router_id: str) -> list:
    data = _get(f"/routers/{router_id}/devices")
    return data.get("devices", []) if data else []


def get_router_hourly_sessions(router_id: str) -> list:
    data = _get(f"/routers/{router_id}/hourly-sessions-duration")
    return data.get("hourly_sessions", []) if data else []


def create_router(router_id: str, name: str, location_x: float, location_y: float) -> tuple[dict | None, str | None]:
    return _post_verbose("/routers", {"router_id": router_id, "name": name,
                                      "location_x": location_x, "location_y": location_y})


# ── Devices ───────────────────────────────────────────────────────────────────
def get_devices() -> list:
    data = _get("/devices")
    return data.get("devices", []) if data else []


def get_devices_with_info() -> list:
    data = _get("/devices/with-routers-info")
    return data.get("devices", []) if data else []


def create_device(device_id: str, name: str) -> tuple[dict | None, str | None]:
    return _post_verbose("/devices", {"device_id": device_id, "name": name})


def release_device(device_id: str) -> bool:
    try:
        r = requests.put(f"{BASE_URL}/devices/{device_id}/release",
                         headers=_auth(), timeout=TIMEOUT)
        r.raise_for_status()
        return True
    except Exception:
        return False


def rename_device(device_id: str, name: str) -> tuple[dict | None, str | None]:
    return _patch_verbose(f"/devices/{device_id}/name", {"name": name})


def reassign_device(device_id: str, patient_id: str | None) -> tuple[dict | None, str | None]:
    return _put_verbose(f"/devices/{device_id}/assign", {"patient_id": patient_id})


# ── Patients ──────────────────────────────────────────────────────────────────
def get_patients() -> list:
    data = _get("/patients")
    return data.get("patients", []) if data else []


def get_patient_sessions(patient_id: str) -> list:
    data = _get(f"/patients/{patient_id}/sessions")
    return data.get("patient_sessions", []) if data else []


def create_patient(name: str, device_id: str) -> tuple[dict | None, str | None]:
    return _post_verbose("/patients", {"name": name, "device_id": device_id})


# ── Demo / fallback data (used when backend returns no rows) ──────────────────

_DEMO_OCC: dict[str, dict[int, int]] = {
    "Reception":    {8:3, 9:5, 10:4, 11:3, 12:2, 13:4, 14:3, 15:2, 16:2, 17:1},
    "Waiting Room": {8:2, 9:6, 10:7, 11:5, 12:3, 13:6, 14:7, 15:5, 16:4, 17:2},
    "Exam Room A":  {8:1, 9:3, 10:4, 11:4, 12:2, 13:3, 14:4, 15:3, 16:2, 17:1},
    "Exam Room B":  {8:1, 9:2, 10:3, 11:4, 12:1, 13:2, 14:3, 15:4, 16:2, 17:1},
    "Pharmacy":     {8:0, 9:1, 10:3, 11:4, 12:5, 13:2, 14:2, 15:4, 16:3, 17:2},
}
_DEMO_ROOMS_HOURLY_OCC = [
    {"router_id": f"demo-{n.lower().replace(' ','-')}",
     "router_name": n, "hour_of_day": h, "patient_count": c}
    for n, hrs in _DEMO_OCC.items()
    for h, c in hrs.items()
]

_DEMO_ROOMS_DWELL = [
    {"router_id": "demo-waiting-room",  "router_name": "Waiting Room",
     "total_sessions": 45, "avg_dwell_seconds": 2400, "total_dwell_seconds": 108000},
    {"router_id": "demo-exam-room-a",   "router_name": "Exam Room A",
     "total_sessions": 20, "avg_dwell_seconds": 1320, "total_dwell_seconds":  26400},
    {"router_id": "demo-exam-room-b",   "router_name": "Exam Room B",
     "total_sessions": 18, "avg_dwell_seconds": 1080, "total_dwell_seconds":  19440},
    {"router_id": "demo-pharmacy",      "router_name": "Pharmacy",
     "total_sessions": 30, "avg_dwell_seconds":  720, "total_dwell_seconds":  21600},
    {"router_id": "demo-reception",     "router_name": "Reception",
     "total_sessions": 50, "avg_dwell_seconds":  300, "total_dwell_seconds":  15000},
]

_DEMO_PATIENTS_ROOM = [
    # Ahmed Ali
    {"patient_id":"p1","patient_name":"Ahmed Ali",    "router_name":"Reception",
     "visit_count":1,"total_seconds":300,  "avg_seconds":300},
    {"patient_id":"p1","patient_name":"Ahmed Ali",    "router_name":"Waiting Room",
     "visit_count":1,"total_seconds":2100, "avg_seconds":2100},
    {"patient_id":"p1","patient_name":"Ahmed Ali",    "router_name":"Exam Room A",
     "visit_count":1,"total_seconds":1200, "avg_seconds":1200},
    {"patient_id":"p1","patient_name":"Ahmed Ali",    "router_name":"Pharmacy",
     "visit_count":1,"total_seconds":600,  "avg_seconds":600},
    # Sara Hassan
    {"patient_id":"p2","patient_name":"Sara Hassan",  "router_name":"Reception",
     "visit_count":1,"total_seconds":240,  "avg_seconds":240},
    {"patient_id":"p2","patient_name":"Sara Hassan",  "router_name":"Waiting Room",
     "visit_count":1,"total_seconds":2520, "avg_seconds":2520},
    {"patient_id":"p2","patient_name":"Sara Hassan",  "router_name":"Exam Room B",
     "visit_count":1,"total_seconds":1500, "avg_seconds":1500},
    # Omar Mahmoud
    {"patient_id":"p3","patient_name":"Omar Mahmoud", "router_name":"Reception",
     "visit_count":1,"total_seconds":360,  "avg_seconds":360},
    {"patient_id":"p3","patient_name":"Omar Mahmoud", "router_name":"Exam Room A",
     "visit_count":2,"total_seconds":2700, "avg_seconds":1350},
    {"patient_id":"p3","patient_name":"Omar Mahmoud", "router_name":"Pharmacy",
     "visit_count":1,"total_seconds":900,  "avg_seconds":900},
    # Laila Ibrahim
    {"patient_id":"p4","patient_name":"Laila Ibrahim","router_name":"Reception",
     "visit_count":1,"total_seconds":180,  "avg_seconds":180},
    {"patient_id":"p4","patient_name":"Laila Ibrahim","router_name":"Waiting Room",
     "visit_count":1,"total_seconds":1680, "avg_seconds":1680},
    {"patient_id":"p4","patient_name":"Laila Ibrahim","router_name":"Exam Room B",
     "visit_count":1,"total_seconds":1080, "avg_seconds":1080},
    {"patient_id":"p4","patient_name":"Laila Ibrahim","router_name":"Pharmacy",
     "visit_count":1,"total_seconds":480,  "avg_seconds":480},
]

_DEMO_AVG_VISIT = {"avg_visit_seconds": 2700, "patient_count": 8}

_DEMO_HOURLY_RECORDS = [
    {"hour": f"2025-01-01T{h:02d}:00:00",
     "records_count": c}
    for h, c in [(8,12),(9,35),(10,48),(11,42),(12,28),(13,31),(14,45),(15,38),(16,22),(17,10)]
]

_DEMO_HOURLY_DEVICES = [
    {"hour": f"2025-01-01T{h:02d}:00:00",
     "patients_count": c}
    for h, c in [(8,3),(9,7),(10,9),(11,8),(12,5),(13,6),(14,8),(15,7),(16,4),(17,2)]
]

_DEMO_HOURLY_SESSIONS = [
    {"hour": f"2025-01-01T{h:02d}:00:00",
     "average_total_session_duration": s}
    for h, s in [(8,1200),(9,2400),(10,2700),(11,3000),(12,1800),
                 (13,2100),(14,2850),(15,2550),(16,2100),(17,1500)]
]

# ── Records ───────────────────────────────────────────────────────────────────
def get_hourly_records() -> list:
    data = _get("/records/hourly-records")
    rows = data.get("records_hourly", []) if data else []
    return rows or _DEMO_HOURLY_RECORDS


def get_hourly_devices() -> list:
    data = _get("/records/hourly-patients")
    rows = data.get("records_hourly", []) if data else []
    return rows or _DEMO_HOURLY_DEVICES


def get_hourly_sessions_duration() -> list:
    data = _get("/records/hourly-sessions-duration")
    rows = data.get("hourly_sessions", []) if data else []
    return rows or _DEMO_HOURLY_SESSIONS


def get_hourly_patients() -> list:
    data = _get("/records/hourly-patients")
    rows = data.get("records_hourly", []) if data else []
    return rows or _DEMO_HOURLY_DEVICES


def get_avg_visit_time() -> dict:
    data = _get("/records/avg-visit-time")
    if data and data.get("patient_count", 0) > 0:
        return data
    return _DEMO_AVG_VISIT


def get_rooms_hourly_occupancy() -> list:
    data = _get("/records/rooms-hourly-occupancy")
    rows = data.get("rooms_hourly_occupancy", []) if data else []
    return rows or _DEMO_ROOMS_HOURLY_OCC


def get_rooms_dwell_time() -> list:
    data = _get("/records/rooms-dwell-time")
    rows = data.get("rooms_dwell_time", []) if data else []
    return rows or _DEMO_ROOMS_DWELL


def get_patients_room_stats() -> list:
    data = _get("/records/patients-room-stats")
    rows = data.get("patients_room_stats", []) if data else []
    return rows or _DEMO_PATIENTS_ROOM


# ── Settings ──────────────────────────────────────────────────────────────────
def get_settings() -> dict | None:
    data = _get("/settings")
    return data.get("settings") if data else None


def update_settings_api(**kwargs) -> bool:
    payload = {k: v for k, v in kwargs.items() if v is not None}
    return _put("/settings", json=payload) is not None


def delete_records() -> bool:
    return _delete("/settings/records", json={"confirm": True})


def delete_account() -> bool:
    return _delete("/settings/account")


def get_blueprint() -> str | None:
    data = _get("/settings/blueprint")
    return data.get("url") if data else None


def upload_blueprint(file_bytes: bytes, filename: str) -> bool:
    try:
        r = requests.put(
            f"{BASE_URL}/settings/blueprint",
            files={"image": (filename, file_bytes)},
            headers=_auth(),
            timeout=30,
        )
        r.raise_for_status()
        return True
    except Exception:
        return False

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


def _put(path: str, json: dict | None = None) -> dict | None:
    try:
        r = requests.put(f"{BASE_URL}{path}", json=json, headers=_auth(), timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _delete(path: str) -> bool:
    try:
        r = requests.delete(f"{BASE_URL}{path}", headers=_auth(), timeout=TIMEOUT)
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


# ── Patients ──────────────────────────────────────────────────────────────────
def get_patients() -> list:
    data = _get("/patients")
    return data.get("patients", []) if data else []


def get_patient_sessions(patient_id: str) -> list:
    data = _get(f"/patients/{patient_id}/sessions")
    return data.get("patient_sessions", []) if data else []


def create_patient(name: str, device_id: str) -> tuple[dict | None, str | None]:
    return _post_verbose("/patients", {"name": name, "device_id": device_id})


# ── Records ───────────────────────────────────────────────────────────────────
def get_hourly_records() -> list:
    data = _get("/records/hourly-records")
    return data.get("records_hourly", []) if data else []


def get_hourly_devices() -> list:
    # Backend has no /hourly-devices; use /hourly-patients (patients ≈ active devices)
    data = _get("/records/hourly-patients")
    return data.get("records_hourly", []) if data else []


def get_hourly_sessions_duration() -> list:
    data = _get("/records/hourly-sessions-duration")
    return data.get("hourly_sessions", []) if data else []


def get_hourly_patients() -> list:
    data = _get("/records/hourly-patients")
    return data.get("records_hourly", []) if data else []


# ── Settings ──────────────────────────────────────────────────────────────────
def get_settings() -> dict | None:
    data = _get("/settings")
    return data.get("settings") if data else None


def update_settings_api(**kwargs) -> bool:
    payload = {k: v for k, v in kwargs.items() if v is not None}
    return _put("/settings", json=payload) is not None


def delete_records() -> bool:
    return _delete("/settings/records")


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

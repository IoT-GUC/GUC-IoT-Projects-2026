/* Web Serial helpers — registered in window.dash_clientside.serial
   Only works in Chrome / Edge (Web Serial API requirement).

   USAGE FLOW:
   1. Go to Settings → "Authorize Scanner" button → pick the ESP32 port once.
      The browser remembers the permission permanently.
   2. On Device Management / Patient Tracking, click Scan.
      navigator.serial.getPorts() silently returns the authorized port — no picker shown.

   Serial line formats accepted:
     "aa:bb:cc:dd:ee:ff -32"  → MAC + RSSI  (ble_scanner_reg sketch)
     "aa:bb:cc:dd:ee:ff"      → MAC only    (beacon printing own MAC in loop)

   minRssi: minimum acceptable RSSI in dBm.
     -40  ≈ 20 cm  (proximity mode — Add Patient)
     -100 = no filter (Device Management, device on USB)
*/


// ── shared scan state ─────────────────────────────────────────────────────────
const MIN_RSSI = -40; // default RSSI threshold for proximity-based patient scans

let _activeScanReader = null;  // set while scan is open so stop_scan can cancel it
let _scanCancelled    = false; // set by stop_scan before cancelling the reader


// ── core scan logic ───────────────────────────────────────────────────────────

async function _serialScan(minRssi) {
    if (!navigator.serial) {
        return { mac: null, status: "Web Serial API not supported — use Chrome or Edge." };
    }

    let port = null;

    // 1. Try to reuse the port authorized in Settings (no picker shown)
    try {
        const saved = await navigator.serial.getPorts();
        if (saved.length > 0) port = saved[0];
    } catch (_) { }

    // 2. Fall back to picker if nothing was pre-authorized
    if (!port) {
        try {
            port = await navigator.serial.requestPort();
        } catch (e) {
            return { mac: null, status: "Port selection cancelled." };
        }
    }

    try {
        await port.open({ baudRate: 115200 });
    } catch (e) {
        return { mac: null, status: "Could not open port: " + e.message };
    }

    const reader = port.readable.getReader();
    _activeScanReader = reader;

    const decoder = new TextDecoder();

    let buffer = "";
    let found  = null;

    const timer = setTimeout(() => reader.cancel(), 3000);

    try {
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            console.log("[serial_scan] raw:", JSON.stringify(chunk));
            buffer += chunk;

            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                const t = line.trim();

                try {
                    const {mac, rssi} = JSON.parse(t);
                    console.log(`[serial_scan] parsed JSON: mac=${mac} rssi=${rssi}`);
                    if (rssi >= minRssi) {
                        found = mac;
                        break;
                    }
                } catch (_) {
                    // Not JSON - neglect parsing errors
                }
            }
            if (found) break;
        }
    } catch (_) { /* reader.cancel() rejects the pending read — expected */ }
    finally {
        clearTimeout(timer);
        _activeScanReader = null;
        try { reader.releaseLock(); } catch (_) { }
        try { await port.close(); } catch (_) { }
    }

    if (found)          return { mac: found, status: "ok" };
    if (_scanCancelled) return { mac: null,  status: null };   // stop_scan already updated UI

    const label = minRssi > MIN_RSSI
        ? "No device detected within range (~20 cm). Hold the device closer and try again."
        : "No MAC address found. Make sure the device is powered and printing output.";
    return { mac: null, status: label };
}


// ── button toggle helpers (DOM — avoids an extra Dash round-trip) ─────────────

function _showScanBtn(scanId, stopId) {
    const s = document.getElementById(scanId);
    const t = document.getElementById(stopId);
    if (s) s.style.display = '';
    if (t) t.style.display = 'none';
}

function _showStopBtn(scanId, stopId) {
    const s = document.getElementById(scanId);
    const t = document.getElementById(stopId);
    if (s) s.style.display = 'none';
    if (t) t.style.display = '';
}


// ── Dash clientside namespace ─────────────────────────────────────────────────

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    serial: {

        // Settings page — authorize the scanner port once so future scans skip the picker
        authorize: function (n_clicks) {
            if (!n_clicks) return "";
            return (async function () {
                if (!navigator.serial) return "Web Serial API not supported — use Chrome or Edge.";
                let port;
                try {
                    port = await navigator.serial.requestPort();
                } catch (e) {
                    return "Cancelled.";
                }
                try {
                    await port.open({ baudRate: 115200 });
                    await port.close();
                    return "ok";
                } catch (e) {
                    return "Could not open port: " + e.message;
                }
            })();
        },

        // Device Management — no RSSI filter (device plugged in via USB)
        scan_device: function (n_clicks) {
            if (!n_clicks) return [window.dash_clientside.no_update, ""];
            _scanCancelled = false;
            _showStopBtn('scan-device-btn', 'stop-scan-btn');
            // Show interim status directly — Dash updates outputs only on Promise resolve
            const st = document.getElementById('dm-scan-status');
            if (st) st.textContent = 'Scanning…';
            return _serialScan(MIN_RSSI).then(function (result) {
                _showScanBtn('scan-device-btn', 'stop-scan-btn');
                if (result.status === "ok")
                    return [result.mac, ""];
                if (result.status === null)   // cancelled — stop_scan already set status text
                    return [window.dash_clientside.no_update, window.dash_clientside.no_update];
                return [window.dash_clientside.no_update, result.status];
            });
        },

        // Stop an in-progress Device Management scan
        stop_scan: function (n_clicks) {
            if (!n_clicks) return window.dash_clientside.no_update;
            _scanCancelled = true;
            if (_activeScanReader) {
                try { _activeScanReader.cancel(); } catch (_) {}
            }
            _showScanBtn('scan-device-btn', 'stop-scan-btn');
            return "Scan cancelled.";
        },

        // Add Patient — -40 dBm ≈ 20 cm proximity filter
        scan_patient: function (n_clicks) {
            if (!n_clicks) return [null, "— not scanned —", ""];
            return _serialScan(-40).then(function (result) {
                if (result.status === "ok") return [result.mac, result.mac, "✓ Device within range"];
                return [null, "— scan failed —", result.status];
            });
        },
    }
});

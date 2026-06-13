/**
 * Extend Navigator interface to include Web Serial API types
 */
declare global {
    interface Navigator {
        serial: any;
    }
}

const MIN_RSSI = Number(import.meta.env.SCAN_MIN_RSSI || -40); // default RSSI threshold for proximity-based patient scans
const BAUD_RATE = Number(import.meta.env.SCAN_BAUD_RATE || 115200);
const SCAN_TIMEOUT = Number(import.meta.env.SCAN_TIMEOUT || 3000);

let _port: any = null;
let _activeScanReader: any = null;



export async function serialScan() {
    if (!navigator.serial) {
        return { mac: null, status: "Web Serial API not supported — use Chrome or Edge." };
    }

    if (_port) {
        return { mac: null, status: "Scan already in progress." };
    }
    if (_activeScanReader) {
        return { mac: null, status: "Scan already in progress." };
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
        await port.open({ baudRate: BAUD_RATE });
    } catch (_) {
        return { mac: null, status: "Could not open port" };
    }
    _port = port;


    const reader = port.readable.getReader();
    _activeScanReader = reader;

    const decoder = new TextDecoder();

    let buffer = "";
    let found = null;

    const timer = setTimeout(() => reader.cancel(), SCAN_TIMEOUT);

    try {
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            console.log("[serial_scan] raw:", JSON.stringify(chunk));
            buffer += chunk;

            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                const t = line.trim();

                try {
                    const { mac, rssi } = JSON.parse(t);
                    console.log(`[serial_scan] parsed JSON: mac=${mac} rssi=${rssi}`);
                    if (rssi >= MIN_RSSI) {
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
        _port = null;
        try { reader.releaseLock(); } catch (_) { }
        try { await port.close(); } catch (_) { }
    }

    if (found) return { mac: found, status: "ok" };

    const label = "No device detected within range (~3 cm). Hold the device closer and try again."
    return { mac: null, status: label };
}


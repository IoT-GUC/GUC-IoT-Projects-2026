import { useState, useEffect, useCallback, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine, CartesianGrid
} from "recharts";

/* ─── API base ─────────────────────────────────────────────────── */
const API = "http://localhost:8000";
const POLL_MS = 3000;  // refresh every 3 s (matches TX interval)

/* ─── Zone config — single floor only ─────────────────────────── */
const ZONES = {
  "Same Room":   { color: "#00C896", glow: "#00C89640", label: "Same Room",   short: "HERE",     order: 0 },
  "Nearby Room": { color: "#4A9EFF", glow: "#4A9EFF40", label: "Nearby Room", short: "NEAR",     order: 1 },
  "Same Floor":  { color: "#FFB547", glow: "#FFB54740", label: "Same Floor",  short: "FAR",      order: 2 },
  "Out of Range":{ color: "#FF5A5A", glow: "#FF5A5A40", label: "Out of Range",short: "OOR",      order: 3 },
};

const STATUS_META = {
  "Active":      { color: "#00C896", dot: "#00C896", label: "Active"      },
  "Idle":        { color: "#FFB547", dot: "#FFB547", label: "Idle"        },
  "Out of Range":{ color: "#FF5A5A", dot: "#FF5A5A", label: "Out of Range"},
};

/* ─── Floor map rooms — (x,y,w,h) in SVG units, viewBox 200×120 ─ */
const FLOOR_ROOMS = [
  {
    id:    "Same Room",
    label: "Office",
    sublabel: "Receiver Room",
    x: 10, y: 15, w: 52, h: 45,
    zones: ["Same Room"],
  },
  {
    id:    "Nearby Room",
    label: "Meeting Room",
    sublabel: "",
    x: 72, y: 15, w: 44, h: 45,
    zones: ["Nearby Room"],
  },
  {
    id:    "Same Floor",
    label: "Corridor / Lab",
    sublabel: "",
    x: 10, y: 70, w: 106, h: 35,
    zones: ["Same Floor"],
  },
];

/* ─── Utilities ────────────────────────────────────────────────── */
function ago(received_at) {
  const s = Math.round(Date.now() / 1000 - received_at);
  if (s < 5)  return "just now";
  if (s < 60) return `${s}s ago`;
  return `${Math.floor(s / 60)}m ago`;
}

function rssiPct(rssi) {
  return Math.round(Math.max(0, Math.min(100, ((rssi + 110) / 70) * 100)));
}

/* ─── Sub-components ───────────────────────────────────────────── */

function PulsingDot({ color }) {
  return (
    <span style={{ position: "relative", display: "inline-flex", width: 10, height: 10, flexShrink: 0 }}>
      <span style={{
        position: "absolute", inset: 0, borderRadius: "50%",
        background: color, opacity: 0.4,
        animation: "ping 1.4s cubic-bezier(0,0,0.2,1) infinite",
      }} />
      <span style={{ borderRadius: "50%", width: 10, height: 10, background: color, position: "relative" }} />
    </span>
  );
}

function ZonePill({ zone, size = "sm" }) {
  const m = ZONES[zone] || ZONES["Out of Range"];
  const pad = size === "lg" ? "5px 14px" : "3px 9px";
  const fs  = size === "lg" ? 13 : 11;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      background: m.glow, color: m.color,
      padding: pad, borderRadius: 20,
      border: `1px solid ${m.color}55`,
      fontSize: fs, fontWeight: 600, letterSpacing: "0.03em",
      fontFamily: "'DM Mono', monospace",
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: m.color, flexShrink: 0 }} />
      {m.label}
    </span>
  );
}

function StatusPill({ status }) {
  const m = STATUS_META[status] || STATUS_META["Out of Range"];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      color: m.color, fontSize: 11, fontWeight: 500,
    }}>
      <PulsingDot color={m.dot} />
      {m.label}
    </span>
  );
}

function RssiBar({ rssi }) {
  const pct   = rssiPct(rssi);
  const color = pct > 60 ? "#00C896" : pct > 35 ? "#FFB547" : "#FF5A5A";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, width: "100%" }}>
      <div style={{
        flex: 1, height: 5, background: "#ffffff12",
        borderRadius: 3, overflow: "hidden",
      }}>
        <div style={{
          width: `${pct}%`, height: "100%",
          background: `linear-gradient(90deg, ${color}aa, ${color})`,
          borderRadius: 3,
          transition: "width 0.5s cubic-bezier(.4,0,.2,1)",
          boxShadow: `0 0 6px ${color}88`,
        }} />
      </div>
      <span style={{
        fontSize: 11, minWidth: 56, textAlign: "right",
        fontFamily: "'DM Mono', monospace",
        color: color,
      }}>{rssi} dBm</span>
    </div>
  );
}

/* ─── Floor Map ────────────────────────────────────────────────── */
function FloorMap({ assetZone, assetId }) {
  const zone    = ZONES[assetZone] || ZONES["Out of Range"];
  const isOOR   = assetZone === "Out of Range" || !assetZone;

  return (
    <div style={{ width: "100%", position: "relative" }}>
      <svg
        viewBox="0 0 200 120"
        style={{ width: "100%", borderRadius: 10, display: "block" }}
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Background */}
        <rect width="200" height="120" fill="#0d1117" rx="8" />

        {/* Grid */}
        {[30,60,90].map(y => (
          <line key={y} x1="0" y1={y} x2="200" y2={y}
            stroke="#ffffff08" strokeWidth="0.5" />
        ))}
        {[50,100,150].map(x => (
          <line key={x} x1={x} y1="0" x2={x} y2="120"
            stroke="#ffffff08" strokeWidth="0.5" />
        ))}

        {/* Receiver marker — top-right corner of office */}
        <circle cx="55" cy="20" r="3" fill="#4A9EFF" opacity="0.8" />
        <text x="60" y="23" fontSize="5" fill="#4A9EFF" opacity="0.8">RX</text>

        {/* Rooms */}
        {FLOOR_ROOMS.map(room => {
          const active = !isOOR && room.zones.includes(assetZone);
          const meta   = ZONES[room.zones[0]];
          return (
            <g key={room.id}>
              {/* Room fill */}
              <rect
                x={room.x} y={room.y} width={room.w} height={room.h}
                rx="3"
                fill={active ? `${meta.color}18` : "#ffffff06"}
                stroke={active ? meta.color : "#ffffff20"}
                strokeWidth={active ? 1.2 : 0.6}
              />
              {/* Room label */}
              <text
                x={room.x + room.w / 2}
                y={room.y + room.h / 2 - (room.sublabel ? 5 : 0)}
                textAnchor="middle" fontSize="6"
                fill={active ? meta.color : "#ffffff55"}
                fontWeight={active ? "600" : "400"}
              >
                {room.label}
              </text>
              {room.sublabel && (
                <text
                  x={room.x + room.w / 2}
                  y={room.y + room.h / 2 + 6}
                  textAnchor="middle" fontSize="4.5"
                  fill={active ? `${meta.color}aa` : "#ffffff33"}
                >
                  {room.sublabel}
                </text>
              )}

              {/* Active room glow */}
              {active && (
                <rect
                  x={room.x} y={room.y} width={room.w} height={room.h}
                  rx="3" fill="none"
                  stroke={meta.color} strokeWidth="2" opacity="0.2"
                >
                  <animate attributeName="opacity" values="0.15;0.35;0.15" dur="2s" repeatCount="indefinite" />
                </rect>
              )}
            </g>
          );
        })}

        {/* Corridors / door openings */}
        <line x1="62" y1="37" x2="72" y2="37" stroke="#ffffff22" strokeWidth="1" strokeDasharray="2 1" />
        <line x1="36" y1="60" x2="36" y2="70" stroke="#ffffff22" strokeWidth="1" strokeDasharray="2 1" />
        <line x1="90" y1="60" x2="90" y2="70" stroke="#ffffff22" strokeWidth="1" strokeDasharray="2 1" />

        {/* Asset dot — placed in the center of the active room */}
        {!isOOR && (() => {
          const room = FLOOR_ROOMS.find(r => r.zones.includes(assetZone));
          if (!room) return null;
          const cx = room.x + room.w / 2;
          const cy = room.y + room.h / 2;
          return (
            <g>
              {/* Outer glow ring */}
              <circle cx={cx} cy={cy} r="8" fill={zone.color} opacity="0.08">
                <animate attributeName="r" values="6;11;6" dur="2.2s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.12;0.04;0.12" dur="2.2s" repeatCount="indefinite" />
              </circle>
              {/* Middle ring */}
              <circle cx={cx} cy={cy} r="5" fill={zone.color} opacity="0.2">
                <animate attributeName="r" values="4;7;4" dur="2.2s" repeatCount="indefinite" />
              </circle>
              {/* Core dot */}
              <circle cx={cx} cy={cy} r="3.5" fill={zone.color} />

              {/* Asset label bubble */}
              <rect
                x={cx - 14} y={cy - 14} width="28" height="9"
                rx="2" fill="#0d1117" stroke={zone.color} strokeWidth="0.6" opacity="0.9"
              />
              <text
                x={cx} y={cy - 7.5}
                textAnchor="middle" fontSize="4.5"
                fill={zone.color} fontWeight="600"
              >
                {assetId || "ASSET"}
              </text>
            </g>
          );
        })()}

        {/* Out-of-range overlay */}
        {isOOR && (
          <g>
            <text x="100" y="60" textAnchor="middle" fontSize="8" fill="#FF5A5A55">
              SIGNAL LOST
            </text>
            <text x="100" y="72" textAnchor="middle" fontSize="5.5" fill="#FF5A5A44">
              Asset out of range
            </text>
          </g>
        )}

        {/* Floor label */}
        <text x="196" y="117" textAnchor="end" fontSize="4" fill="#ffffff22">FLOOR 1</text>
      </svg>
    </div>
  );
}

/* ─── RSSI Chart tooltip ───────────────────────────────────────── */
function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const z = ZONES[payload[0]?.payload?.zone] || ZONES["Out of Range"];
  return (
    <div style={{
      background: "#161b22", border: `1px solid ${z.color}44`,
      borderRadius: 8, padding: "8px 12px", fontSize: 11,
      fontFamily: "'DM Mono', monospace",
    }}>
      <div style={{ color: "#8b949e", marginBottom: 2 }}>{payload[0].payload.timestamp}</div>
      <div style={{ color: z.color, fontWeight: 600 }}>{payload[0].value} dBm</div>
      <div style={{ color: z.color, fontSize: 10, marginTop: 2 }}>{payload[0].payload.zone}</div>
    </div>
  );
}

/* ─── Asset Card ───────────────────────────────────────────────── */
function AssetCard({ asset, selected, onClick }) {
  const z   = ZONES[asset.zone]   || ZONES["Out of Range"];
  const s   = STATUS_META[asset.status] || STATUS_META["Out of Range"];
  const ref = useRef(null);

  // Flash animation on new data
  useEffect(() => {
    if (!ref.current) return;
    ref.current.style.transition = "box-shadow 0.1s";
    ref.current.style.boxShadow  = `0 0 16px ${z.color}55`;
    setTimeout(() => {
      if (ref.current) ref.current.style.boxShadow = selected
        ? `0 0 0 1.5px ${z.color}, 0 4px 24px ${z.color}22`
        : "0 1px 4px #00000044";
    }, 400);
  }, [asset.received_at]);

  return (
    <div
      ref={ref}
      onClick={onClick}
      style={{
        background: selected ? "#161b22" : "#0d1117",
        border: selected ? `1.5px solid ${z.color}` : "1px solid #30363d",
        borderRadius: 12,
        padding: "14px 16px",
        cursor: "pointer",
        transition: "border-color 0.2s, box-shadow 0.2s",
        boxShadow: selected ? `0 0 0 1.5px ${z.color}, 0 4px 24px ${z.color}22` : "0 1px 4px #00000044",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
        <div>
          <div style={{
            fontFamily: "'DM Mono', monospace",
            fontWeight: 700, fontSize: 14, color: "#e6edf3",
            letterSpacing: "0.04em",
          }}>
            {asset.asset_id}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
            <StatusPill status={asset.status} />
            <span style={{ fontSize: 10, color: "#8b949e", fontFamily: "'DM Mono', monospace" }}>
              {ago(asset.received_at)}
            </span>
          </div>
        </div>
        <ZonePill zone={asset.zone} />
      </div>

      <RssiBar rssi={asset.rssi} />

      {asset.snr != null && (
        <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
          <span style={{ fontSize: 10, color: "#8b949e", fontFamily: "'DM Mono', monospace" }}>
            SNR {Number(asset.snr).toFixed(1)} dB
          </span>
          {asset.battery != null && (
            <span style={{ fontSize: 10, color: "#8b949e", fontFamily: "'DM Mono', monospace" }}>
              BAT {Number(asset.battery).toFixed(2)} V
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Main App ─────────────────────────────────────────────────── */
export default function App() {
  const [overview,      setOverview]      = useState([]);
  const [selected,      setSelected]      = useState(null);
  const [history,       setHistory]       = useState([]);
  const [stats,         setStats]         = useState({});
  const [thresholds,    setThresholds]    = useState(null);
  const [editThresh,    setEditThresh]    = useState(false);
  const [thresh,        setThresh]        = useState({});
  const [loading,       setLoading]       = useState(true);
  const [lastRefresh,   setLastRefresh]   = useState(null);
  const [error,         setError]         = useState(null);
  const [liveIndicator, setLiveIndicator] = useState(false);

  const selectedAsset = overview.find(a => a.asset_id === selected);
  const selectedStats = stats[selected];

  /* ── Data fetching ─────────────────────────────────────────── */
  const fetchAll = useCallback(async () => {
    try {
      const [ovRes, stRes, thRes] = await Promise.all([
        fetch(`${API}/overview`),
        fetch(`${API}/stats`),
        fetch(`${API}/thresholds`),
      ]);
      const [ovData, stData, thData] = await Promise.all([
        ovRes.json(), stRes.json(), thRes.json(),
      ]);

      setOverview(ovData.assets || []);
      const statsMap = {};
      (stData.stats || []).forEach(s => { statsMap[s.asset_id] = s; });
      setStats(statsMap);
      setThresholds(thData);
      if (!thresh.same_room) setThresh(thData);
      setError(null);
    } catch (e) {
      setError("Cannot reach backend at " + API + " — is it running?");
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
      // pulse live indicator
      setLiveIndicator(true);
      setTimeout(() => setLiveIndicator(false), 600);
    }
  }, [thresh.same_room]);

  const fetchHistory = useCallback(async (id) => {
    if (!id) return;
    try {
      const res  = await fetch(`${API}/assets/${id}/history?limit=40`);
      const data = await res.json();
      // reverse so oldest-first for chart
      setHistory([...(data.history || [])].reverse());
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const iv = setInterval(fetchAll, POLL_MS);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    fetchHistory(selected);
  }, [selected, overview]);  // re-fetch history when overview updates

  /* ── Threshold save ────────────────────────────────────────── */
  const saveThresholds = async () => {
    try {
      await fetch(`${API}/thresholds`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          same_room:   Number(thresh.same_room),
          nearby_room: Number(thresh.nearby_room),
          same_floor:  Number(thresh.same_floor),
        }),
      });
      setEditThresh(false);
      fetchAll();
    } catch {
      alert("Failed to save thresholds");
    }
  };

  /* ── Zone reference lines for chart ─────────────────────────── */
  const zoneLines = thresholds ? [
    { y: thresholds.same_room,   color: "#00C896", label: "Same Room"   },
    { y: thresholds.nearby_room, color: "#4A9EFF", label: "Nearby"      },
    { y: thresholds.same_floor,  color: "#FFB547", label: "Same Floor"  },
  ] : [];

  /* ── Styles ──────────────────────────────────────────────────── */
  const card = {
    background: "#0d1117",
    border: "1px solid #21262d",
    borderRadius: 12,
    padding: "1rem 1.2rem",
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#010409",
      color: "#e6edf3",
      fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
      padding: "0",
    }}>
      {/* ── CSS keyframes injected ── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
        @keyframes ping {
          75%, 100% { transform: scale(2); opacity: 0; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0);   }
        }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #010409; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
        input[type=number] {
          background: #161b22; border: 1px solid #30363d; color: #e6edf3;
          border-radius: 6px; padding: 6px 10px; font-size: 12px; width: 100%;
          font-family: 'DM Mono', monospace;
        }
        input[type=number]:focus { outline: none; border-color: #4A9EFF; }
      `}</style>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div style={{
        borderBottom: "1px solid #21262d",
        padding: "0 24px",
        height: 56,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, zIndex: 100,
        background: "#010409cc",
        backdropFilter: "blur(12px)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* Logo mark */}
          <div style={{
            width: 28, height: 28, borderRadius: 7,
            background: "linear-gradient(135deg, #00C896, #4A9EFF)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="2.5" fill="white" />
              <circle cx="7" cy="7" r="5" stroke="white" strokeWidth="1.2" fill="none" opacity="0.5" />
              <circle cx="7" cy="7" r="7" stroke="white" strokeWidth="0.6" fill="none" opacity="0.2" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: "0.01em" }}>
              LoRa Asset Locator
            </div>
            <div style={{ fontSize: 10, color: "#8b949e", marginTop: -1 }}>
              Indoor positioning system · Floor 1
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {/* Live indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "#8b949e" }}>
            <span style={{
              width: 7, height: 7, borderRadius: "50%",
              background: liveIndicator ? "#00C896" : "#30363d",
              transition: "background 0.3s",
              boxShadow: liveIndicator ? "0 0 8px #00C896" : "none",
            }} />
            {lastRefresh ? `${lastRefresh.toLocaleTimeString()}` : "—"}
          </div>

          <button
            onClick={() => { setEditThresh(e => !e); }}
            style={{
              background: editThresh ? "#21262d" : "transparent",
              border: "1px solid #30363d",
              color: "#8b949e", borderRadius: 7,
              padding: "5px 12px", fontSize: 12, cursor: "pointer",
              fontFamily: "'DM Mono', monospace",
            }}
          >
            Thresholds
          </button>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "20px 24px" }}>

        {/* ── Error banner ─────────────────────────────────────── */}
        {error && (
          <div style={{
            background: "#FF5A5A18", border: "1px solid #FF5A5A44",
            borderRadius: 10, padding: "10px 14px",
            fontSize: 12, marginBottom: 16, color: "#FF5A5A",
            fontFamily: "'DM Mono', monospace",
            animation: "fadeIn 0.3s ease",
          }}>
            ⚠ {error}
          </div>
        )}

        {/* ── Threshold editor ──────────────────────────────────── */}
        {editThresh && thresholds && (
          <div style={{ ...card, marginBottom: 16, animation: "fadeIn 0.2s ease" }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 12, color: "#8b949e", letterSpacing: "0.08em" }}>
              RSSI ZONE THRESHOLDS (dBm)
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 12 }}>
              {[
                ["same_room",   "Same Room",   "#00C896"],
                ["nearby_room", "Nearby Room", "#4A9EFF"],
                ["same_floor",  "Same Floor",  "#FFB547"],
              ].map(([key, label, color]) => (
                <div key={key}>
                  <div style={{ fontSize: 10, color, marginBottom: 4, fontFamily: "'DM Mono', monospace", fontWeight: 600 }}>
                    {label}
                  </div>
                  <input
                    type="number" value={thresh[key] ?? ""}
                    min={-140} max={-20}
                    onChange={e => setThresh(t => ({ ...t, [key]: Number(e.target.value) }))}
                  />
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={saveThresholds} style={{
                background: "#00C896", color: "#010409", border: "none",
                borderRadius: 7, padding: "7px 16px", fontSize: 12,
                fontWeight: 600, cursor: "pointer", fontFamily: "'DM Mono', monospace",
              }}>Save</button>
              <button onClick={() => setEditThresh(false)} style={{
                background: "transparent", color: "#8b949e",
                border: "1px solid #30363d",
                borderRadius: 7, padding: "7px 16px", fontSize: 12, cursor: "pointer",
              }}>Cancel</button>
            </div>
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: "center", padding: "5rem", color: "#8b949e" }}>
            <div style={{
              width: 32, height: 32, border: "2.5px solid #30363d",
              borderTopColor: "#00C896", borderRadius: "50%",
              animation: "spin 0.8s linear infinite", margin: "0 auto 12px",
            }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); }}`}</style>
            <div style={{ fontSize: 13 }}>Connecting to backend…</div>
          </div>
        ) : overview.length === 0 ? (
          <div style={{
            textAlign: "center", padding: "5rem",
            color: "#8b949e", animation: "fadeIn 0.4s ease",
          }}>
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" style={{ margin: "0 auto 12px" }}>
              <circle cx="20" cy="20" r="18" stroke="#30363d" strokeWidth="2" />
              <circle cx="20" cy="20" r="10" stroke="#30363d" strokeWidth="1.5" strokeDasharray="3 2" />
              <circle cx="20" cy="20" r="3" fill="#30363d" />
            </svg>
            <div style={{ fontSize: 14, fontWeight: 500 }}>No assets detected yet</div>
            <div style={{ fontSize: 11, marginTop: 6, fontFamily: "'DM Mono', monospace" }}>
              POST to {API}/telemetry — or power on the sender
            </div>
          </div>
        ) : (
          <>
            {/* ── Summary stats ────────────────────────────────── */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 10, marginBottom: 18,
              animation: "fadeIn 0.4s ease",
            }}>
              {[
                {
                  label: "ASSETS TRACKED",
                  value: overview.length,
                  color: "#e6edf3",
                },
                {
                  label: "ONLINE NOW",
                  value: overview.filter(a => a.status === "Active").length,
                  color: "#00C896",
                  sub: "active in last 15s",
                },
                {
                  label: "BEST SIGNAL",
                  value: `${Math.max(...overview.map(a => a.rssi))} dBm`,
                  color: "#4A9EFF",
                },
                {
                  label: "ZONES IN USE",
                  value: new Set(overview.filter(a => a.status === "Active").map(a => a.zone)).size,
                  color: "#FFB547",
                },
              ].map(({ label, value, color, sub }) => (
                <div key={label} style={{ ...card }}>
                  <div style={{
                    fontSize: 9, color: "#8b949e", letterSpacing: "0.1em",
                    fontFamily: "'DM Mono', monospace", marginBottom: 6,
                  }}>
                    {label}
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 700, color, lineHeight: 1 }}>
                    {value}
                  </div>
                  {sub && <div style={{ fontSize: 10, color: "#8b949e", marginTop: 4 }}>{sub}</div>}
                </div>
              ))}
            </div>

            {/* ── Main grid ────────────────────────────────────── */}
            <div style={{
              display: "grid",
              gridTemplateColumns: selected ? "300px 1fr" : "1fr",
              gap: 14,
              alignItems: "start",
              animation: "fadeIn 0.3s ease",
            }}>
              {/* Asset list */}
              <div>
                <div style={{
                  fontSize: 10, color: "#8b949e", letterSpacing: "0.08em",
                  fontFamily: "'DM Mono', monospace",
                  marginBottom: 8,
                }}>
                  {overview.length} ASSET{overview.length !== 1 ? "S" : ""} · CLICK TO INSPECT
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {overview.map(a => (
                    <AssetCard
                      key={a.asset_id}
                      asset={a}
                      selected={selected === a.asset_id}
                      onClick={() => setSelected(s => s === a.asset_id ? null : a.asset_id)}
                    />
                  ))}
                </div>
              </div>

              {/* Detail panel */}
              {selected && selectedAsset && (
                <div style={{ display: "flex", flexDirection: "column", gap: 12, animation: "fadeIn 0.25s ease" }}>

                  {/* Floor map */}
                  <div style={card}>
                    <div style={{
                      display: "flex", justifyContent: "space-between",
                      alignItems: "center", marginBottom: 12,
                    }}>
                      <div>
                        <div style={{ fontSize: 11, color: "#8b949e", letterSpacing: "0.08em", fontFamily: "'DM Mono', monospace", marginBottom: 2 }}>
                          ESTIMATED LOCATION
                        </div>
                        <div style={{ fontSize: 15, fontWeight: 600, color: "#e6edf3" }}>
                          {selectedAsset.asset_id}
                        </div>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5 }}>
                        <ZonePill zone={selectedAsset.zone} size="lg" />
                        <StatusPill status={selectedAsset.status} />
                      </div>
                    </div>
                    <FloorMap assetZone={selectedAsset.zone} assetId={selectedAsset.asset_id} />

                    {/* Zone legend */}
                    <div style={{ display: "flex", gap: 10, marginTop: 10, flexWrap: "wrap" }}>
                      {Object.entries(ZONES).filter(([k]) => k !== "Out of Range").map(([k, v]) => (
                        <div key={k} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: "#8b949e" }}>
                          <span style={{ width: 8, height: 8, borderRadius: "50%", background: v.color }} />
                          {v.label}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Stats row */}
                  {selectedStats && (
                    <div style={{ display: "grid", gridTemplateColumns: `repeat(${selectedStats.avg_battery != null ? 4 : 3}, 1fr)`, gap: 10 }}>
                      {[
                        { label: "TOTAL PACKETS", value: selectedStats.total_packets },
                        { label: "AVG RSSI",       value: `${Number(selectedStats.avg_rssi).toFixed(1)} dBm` },
                        { label: "BEST RSSI",      value: `${selectedStats.best_rssi} dBm` },
                        ...(selectedStats.avg_battery != null
                          ? [{ label: "AVG BATTERY", value: `${Number(selectedStats.avg_battery).toFixed(2)} V` }]
                          : []),
                      ].map(({ label, value }) => (
                        <div key={label} style={{ ...card, padding: "12px 14px" }}>
                          <div style={{
                            fontSize: 9, color: "#8b949e", letterSpacing: "0.1em",
                            fontFamily: "'DM Mono', monospace", marginBottom: 6,
                          }}>{label}</div>
                          <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "'DM Mono', monospace" }}>
                            {value}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* RSSI history chart */}
                  {history.length > 0 && (
                    <div style={card}>
                      <div style={{
                        fontSize: 11, color: "#8b949e", letterSpacing: "0.08em",
                        fontFamily: "'DM Mono', monospace", marginBottom: 12,
                      }}>
                        RSSI HISTORY · {selectedAsset.asset_id} · last {history.length} readings
                      </div>
                      <div style={{ height: 180 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={history} margin={{ top: 4, right: 12, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                            <XAxis
                              dataKey="timestamp"
                              tick={{ fontSize: 9, fill: "#8b949e", fontFamily: "'DM Mono', monospace" }}
                              interval="preserveStartEnd"
                              axisLine={{ stroke: "#30363d" }}
                              tickLine={false}
                            />
                            <YAxis
                              domain={[-115, -45]}
                              tick={{ fontSize: 9, fill: "#8b949e", fontFamily: "'DM Mono', monospace" }}
                              axisLine={{ stroke: "#30363d" }}
                              tickLine={false}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            {zoneLines.map(zl => (
                              <ReferenceLine
                                key={zl.y} y={zl.y}
                                stroke={zl.color} strokeDasharray="4 3" strokeOpacity={0.5}
                                label={{ value: zl.label, fontSize: 9, fill: zl.color, position: "insideTopRight" }}
                              />
                            ))}
                            <Line
                              type="monotone" dataKey="rssi"
                              stroke="#4A9EFF" strokeWidth={2}
                              dot={false}
                              activeDot={{ r: 4, fill: "#4A9EFF", stroke: "#010409", strokeWidth: 2 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                      {/* Zone color legend */}
                      <div style={{ display: "flex", gap: 14, marginTop: 8, flexWrap: "wrap" }}>
                        {zoneLines.map(zl => (
                          <span key={zl.label} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: "#8b949e" }}>
                            <span style={{ width: 16, height: 1.5, background: zl.color, display: "inline-block", opacity: 0.7 }} />
                            {zl.label} ({zl.y} dBm)
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recent readings table */}
                  {history.length > 0 && (
                    <div style={card}>
                      <div style={{
                        fontSize: 11, color: "#8b949e", letterSpacing: "0.08em",
                        fontFamily: "'DM Mono', monospace", marginBottom: 10,
                      }}>
                        RECENT READINGS
                      </div>
                      <div style={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, fontFamily: "'DM Mono', monospace" }}>
                          <thead>
                            <tr>
                              {["Time", "RSSI", "SNR", "Battery", "Zone"].map(h => (
                                <th key={h} style={{
                                  textAlign: "left", padding: "4px 8px",
                                  color: "#8b949e", fontWeight: 500,
                                  borderBottom: "1px solid #21262d", whiteSpace: "nowrap",
                                }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {[...history].reverse().slice(0, 10).map((r, i) => {
                              const z = ZONES[r.zone] || ZONES["Out of Range"];
                              return (
                                <tr key={r.id} style={{ background: i % 2 === 0 ? "transparent" : "#ffffff04" }}>
                                  <td style={{ padding: "4px 8px", color: "#8b949e" }}>{r.timestamp}</td>
                                  <td style={{ padding: "4px 8px", color: z.color }}>{r.rssi} dBm</td>
                                  <td style={{ padding: "4px 8px", color: "#8b949e" }}>{r.snr != null ? `${Number(r.snr).toFixed(1)} dB` : "—"}</td>
                                  <td style={{ padding: "4px 8px", color: "#8b949e" }}>{r.battery != null ? `${Number(r.battery).toFixed(2)} V` : "—"}</td>
                                  <td style={{ padding: "4px 8px" }}><ZonePill zone={r.zone} /></td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
"""
Streamlit Frontend — reads meter_data.json and displays live dashboard
with gauge-style indicators for each metric.

Run:
    streamlit run frontend.py
"""

import json
import os
import time
import numpy as np
import plotly.graph_objects as go

import streamlit as st
import plotly.graph_objects as go

# ── Configuration ────────────────────────────────────────────────
DATA_FILE = "meter_data.json"

st.set_page_config(
    page_title="Meter Dashboard",
    page_icon="📡",
    layout="wide"
)

# ── Load data ─────────────────────────────────────────────────────
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def make_gauge(value, label, min_val, max_val, unit, color):
    try:
        value = float(value)
    except:
        value = min_val

    # Clamp
    value = max(min_val, min(max_val, value))

    # Convert to percentage
    pct = (value - min_val) / (max_val - min_val)

    # Arc angles
    start_angle = np.pi
    end_angle = np.pi * (1 - pct)

    outer_r = 1.0
    inner_r = 0.72

    # Background arc
    bg_theta = np.linspace(np.pi, 0, 200)

    bg_outer_x = outer_r * np.cos(bg_theta)
    bg_outer_y = outer_r * np.sin(bg_theta)

    bg_inner_x = inner_r * np.cos(bg_theta[::-1])
    bg_inner_y = inner_r * np.sin(bg_theta[::-1])

    # Value arc
    theta = np.linspace(start_angle, end_angle, 200)

    arc_outer_x = outer_r * np.cos(theta)
    arc_outer_y = outer_r * np.sin(theta)

    arc_inner_x = inner_r * np.cos(theta[::-1])
    arc_inner_y = inner_r * np.sin(theta[::-1])

    fig = go.Figure()

    # Background ring
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([bg_outer_x, bg_inner_x]),
            y=np.concatenate([bg_outer_y, bg_inner_y]),
            fill="toself",
            fillcolor="#1a2035",   # dark background ring
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Value ring
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([arc_outer_x, arc_inner_x]),
            y=np.concatenate([arc_outer_y, arc_inner_y]),
            fill="toself",
            fillcolor=color,       # use passed color
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    # Numeric value
    fig.add_annotation(
        x=0,
        y=0.15,
        text=f"{value:.0f}{unit}",
        showarrow=False,
        font=dict(
            size=28,
            color="#e0e8ff"
        )
    )

    # Label
    fig.add_annotation(
        x=0,
        y=-0.28,
        text=label,
        showarrow=False,
        font=dict(
            size=10,
            color="#FFFFFF"
        )
    )

    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        xaxis=dict(
            visible=False,
            range=[-1.2, 1.2]
        ),
        yaxis=dict(
            visible=False,
            range=[-0.35, 1.2],
            scaleanchor="x",
            scaleratio=1
        )
    )

    return fig

# ── Header ────────────────────────────────────────────────────────
st.title("⬡ METER DASHBOARD")
st.caption("LORA · MQTT · REAL-TIME TELEMETRY")

data = load_data()

if not data:
    st.info("⏳ Waiting for data... Make sure backend.py and Mosquitto are running.")
    time.sleep(3)
    st.rerun()

# ── Device selector ───────────────────────────────────────────────
device_ids = list(data.keys())
selected = st.selectbox("DEVICE", device_ids)
readings = data.get(selected, [])

if not readings:
    st.warning(f"No readings for {selected}")
    st.stop()

latest = readings[-1]

# ── Timestamp ─────────────────────────────────────────────────────
ts = latest.get("timestamp", "—")
status = latest.get("status", "UNKNOWN")

if str(status).upper() == "READY":
    st.success(f"🕐 Last Packet: {ts} | 📶 Status: {status}")
else:
    st.error(f"🕐 Last Packet: {ts} | 📶 Status: {status}")

# ── Gauges row ────────────────────────────────────────────────────
reading_val = latest.get("reading", "0")
rssi_val    = latest.get("rssi", -120)
conf        = latest.get("conf", "—")

g1, g2, g3 = st.columns(3)

with g1:
    st.plotly_chart(
        make_gauge(reading_val, "METER READING", 0, 500, "", "#7eb8f7"),
        width="stretch", key="g1"
    )

with g2:
    st.plotly_chart(
        make_gauge(rssi_val, "LORA RSSI", -120, 0, " dBm", "#f472b6"),
        width="stretch", key="g2"
    )

with g3:
    try:
        conf_num = float(conf) * 100
    except (TypeError, ValueError):
        conf_num = 0

    if conf_num >= 80:
        conf_color = "#22c55e"   # green
    elif conf_num >= 50:
        conf_color = "#f59e0b"   # orange
    else:
        conf_color = "#ef4444"   # red

    st.plotly_chart(
        make_gauge(conf_num, "CONFIDENCE", 0, 100, "%", conf_color),
        width="stretch", key="g3"
    )


st.divider()

# ── Time series graphs ────────────────────────────────────────────
rssi_vals     = [r.get("rssi")      for r in readings if r.get("rssi")    is not None]
rssi_times    = [r.get("timestamp") for r in readings if r.get("rssi")    is not None]
reading_vals  = []
reading_times = []
for r in readings:
    try:
        reading_vals.append(float(r.get("reading")))
        reading_times.append(r.get("timestamp"))
    except (TypeError, ValueError):
        pass

def line_chart(x, y, name, color, y_title):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            name=name,
            line=dict(
                color=color,
                width=2
            ),
            marker=dict(
                size=5
            )
        )
    )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=y_title,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="white",
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        ),
        yaxis=dict(
            gridcolor="#333"
        ),
        xaxis=dict(
            gridcolor="#333"
        )
    )

    return fig

col_left, col_right = st.columns(2)
with col_left:
    st.subheader("Reading History")

    st.plotly_chart(
        line_chart(
            reading_times,
            reading_vals,
            "Reading",
            "#f77f00",
            "Reading"
        ),
        width="stretch",
        key="lc1"
    )

with col_right:
    st.subheader("RSSI HISTORY")

    st.plotly_chart(
        line_chart(
            rssi_times,
            rssi_vals,
            "RSSI (dBm)",
            "#00b4d8",
            "dBm"
        ),
        width="stretch",
        key="lc2"
    )

# ── Raw log ───────────────────────────────────────────────────────
with st.expander("📋 RAW PACKET LOG"):
    st.dataframe(list(reversed(readings)), width="stretch")

# ── Refresh ───────────────────────────────────────────────────────
time.sleep(3)
st.rerun()

from datetime import datetime, timezone

import dash
from dash import dcc, html
import plotly.graph_objects as go
import api


def _parse_ts(ts_str: str) -> datetime | None:
    s = (ts_str or "").strip().replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:len(fmt)], fmt)
        except ValueError:
            continue
    return None


def _relative_time(ts_str: str) -> str:
    dt = _parse_ts(ts_str)
    if dt is None:
        return ts_str[:16] if ts_str else "—"
    diff = int((datetime.now() - dt).total_seconds())
    if diff <= 0:    return "just now"
    if diff < 60:    return f"{diff}s ago"
    if diff < 3600:  return f"{diff // 60}m ago"
    if diff < 86400: return f"{diff // 3600}h ago"
    return f"{diff // 86400}d ago"


def _device_status(ts_str: str) -> tuple[str, str]:
    dt = _parse_ts(ts_str)
    if dt is None:
        return "Offline", "badge-offline"
    diff = (datetime.now() - dt).total_seconds()
    if diff <= 0 or diff < 3600:  return "Active", "badge-active"
    if diff < 86400:              return "Idle",   "badge-idle"
    return "Offline", "badge-offline"

dash.register_page(__name__, path="/analytics", title="Analytics — Central Link")

CHART_LAYOUT = dict(
    paper_bgcolor="#1c2230",
    plot_bgcolor="#1c2230",
    font=dict(color="#8b949e", size=10),
    margin=dict(l=40, r=16, t=16, b=40),
    showlegend=True,
    legend=dict(orientation="h", x=0, y=1.12, font=dict(size=10)),
    xaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
    yaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
    height=220,
)


def _fmt_hour(val) -> str:
    """Extract HH:MM from Oracle TIMESTAMP strings or datetime objects."""
    if hasattr(val, "strftime"):
        return val.strftime("%H:%M")
    s = str(val or "").strip()
    for sep in ("T", " "):
        if sep in s:
            return s.split(sep)[1][:5]
    return s[-8:-3] if len(s) >= 8 else s


def records_trend_fig(hourly: list) -> go.Figure:
    hours  = [_fmt_hour(h.get("hour", "")) for h in hourly]
    counts = [h.get("records_count", 0) for h in hourly]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=counts, mode="lines",
        line=dict(color="#9d5cf5", width=2),
        fill="tozeroy", fillcolor="rgba(157,92,245,0.08)",
        name="Primary Hub",
    ))
    fig.update_layout(**CHART_LAYOUT, title=None)
    return fig


def devices_bar_fig(hourly: list) -> go.Figure:
    hours  = [_fmt_hour(h.get("hour", "")) for h in hourly]
    counts = [h.get("patients_count", 0) or h.get("devices_count", 0) for h in hourly]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=hours, y=counts,
        marker_color=["#1f6feb" if i < len(counts) - 1 else "#58a6ff"
                      for i in range(len(counts))],
        name="Active Devices",
    ))
    fig.update_layout(**CHART_LAYOUT, bargap=0.25)
    return fig


def _parse_duration_seconds(dur) -> float:
    """Convert seconds (number) or 'HH:MM:SS' string to seconds."""
    if isinstance(dur, (int, float)):
        return max(0.0, float(dur))
    dur_str = str(dur or "").strip()
    if "T" in dur_str:
        dur_str = dur_str.split("T")[-1]
    dur_str = dur_str.replace("Z", "").strip()
    try:
        parts = dur_str.split(":")
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        return max(0.0, h * 3600 + m * 60 + s)
    except Exception:
        try:
            return max(0.0, float(dur_str))
        except Exception:
            return 0.0


def session_duration_fig(hourly: list) -> go.Figure:
    hours   = [_fmt_hour(h.get("hour", "")) for h in hourly]
    dur_raw = [h.get("average_total_session_duration", "0") for h in hourly]
    minutes = [round(_parse_duration_seconds(d) / 60, 1) for d in dur_raw]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=minutes, mode="lines+markers",
        line=dict(color="#3fb950", width=2),
        marker=dict(size=5, color="#3fb950"),
        fill="tozeroy", fillcolor="rgba(63,185,80,0.07)",
        name="Avg Session (min)",
    ))
    fig.update_layout(**{**CHART_LAYOUT,
                         "yaxis": dict(gridcolor="#21262d", zeroline=False,
                                       ticksuffix="m", tickfont=dict(size=9))})
    return fig


_ROOM_COLORS = ["#1f6feb", "#3fb950", "#e3b341", "#f85149", "#9d5cf5", "#58a6ff", "#f0883e"]


def _fmt_seconds(sec) -> str:
    s = int(sec or 0)
    if s < 60:   return f"{s}s"
    if s < 3600: return f"{s // 60}m {s % 60}s"
    return f"{s // 3600}h {(s % 3600) // 60}m"


def rooms_occupancy_fig(occupancy: list) -> go.Figure:
    """Grouped bar: unique patients per room per hour of day."""
    rooms: dict[str, dict] = {}
    for row in occupancy:
        name = row.get("router_name", "Unknown")
        rooms.setdefault(name, {"hours": [], "counts": []})
        rooms[name]["hours"].append(int(row.get("hour_of_day", 0)))
        rooms[name]["counts"].append(row.get("patient_count", 0))

    fig = go.Figure()
    for i, (name, d) in enumerate(rooms.items()):
        pairs  = sorted(zip(d["hours"], d["counts"]))
        hours  = [f"{h:02d}:00" for h, _ in pairs]
        counts = [c for _, c in pairs]
        fig.add_trace(go.Bar(
            x=hours, y=counts, name=name,
            marker_color=_ROOM_COLORS[i % len(_ROOM_COLORS)],
        ))
    fig.update_layout(**{**CHART_LAYOUT, "height": 260, "barmode": "group", "bargap": 0.2})
    return fig


def rooms_dwell_fig(dwell: list) -> go.Figure:
    """Horizontal bar: rooms ranked by average dwell time (minutes)."""
    fig = go.Figure()
    if not dwell:
        fig.update_layout(**CHART_LAYOUT)
        return fig
    names   = [r.get("router_name", "?") for r in reversed(dwell)]
    avg_min = [round(r.get("avg_dwell_seconds", 0) / 60, 1) for r in reversed(dwell)]
    fig.add_trace(go.Bar(
        x=avg_min, y=names, orientation="h",
        marker=dict(
            color=avg_min,
            colorscale=[[0, "#1f6feb"], [0.5, "#e3b341"], [1, "#f85149"]],
            showscale=False,
        ),
        text=[f"{m}m" for m in avg_min],
        textposition="outside",
        name="Avg Dwell",
    ))
    h = max(180, 60 + len(names) * 36)
    fig.update_layout(**{
        **CHART_LAYOUT,
        "height": h,
        "showlegend": False,
        "xaxis": dict(gridcolor="#21262d", zeroline=False,
                      ticksuffix="m", tickfont=dict(size=9)),
        "yaxis": dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
        "margin": dict(l=90, r=40, t=10, b=30),
    })
    return fig


def layout():
    hourly_records    = api.get_hourly_records()
    hourly_devices    = api.get_hourly_devices()
    hourly_sessions   = api.get_hourly_sessions_duration()
    routers           = api.get_routers()
    devices           = api.get_devices_with_info()
    routers_map       = api.get_routers_map()
    rooms_occupancy   = api.get_rooms_hourly_occupancy()
    rooms_dwell       = api.get_rooms_dwell_time()
    patients_room_stats = api.get_patients_room_stats()

    total_nodes    = len(devices)
    active_routers = sum(1 for r in routers_map if r.get("connected_devices_count", 0) > 0)
    total_routers  = len(routers)
    network_load   = round((active_routers / total_routers * 100) if total_routers else 0, 1)

    trend_fig      = records_trend_fig(hourly_records)
    bar_fig        = devices_bar_fig(hourly_devices)
    session_fig    = session_duration_fig(hourly_sessions)
    occupancy_fig  = rooms_occupancy_fig(rooms_occupancy)
    dwell_fig      = rooms_dwell_fig(rooms_dwell)

    device_rows = []
    for d in devices[:20]:
        ts = str(d.get("last_record_timestamp") or "")
        status, badge = _device_status(ts)
        device_rows.append(html.Tr([
            html.Td(html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px"}, children=[
                html.Div(
                    (d.get("name") or "?")[0].upper(),
                    style={"width": "30px", "height": "30px", "borderRadius": "50%",
                           "background": "linear-gradient(135deg,#e67e22,#d29922)",
                           "display": "flex", "alignItems": "center", "justifyContent": "center",
                           "fontSize": "11px", "fontWeight": 700, "color": "#fff", "flexShrink": 0},
                ),
                html.Div([
                    html.Div(d.get("name", "—"), style={"fontWeight": 600, "fontSize": "13px"}),
                    html.Div(d.get("id", "—")[:20], style={"fontSize": "10px", "color": "var(--text-muted)"}),
                ]),
            ])),
            html.Td(d.get("router_name", "—"), style={"fontSize": "12px"}),
            html.Td(html.Span(status, className=badge)),
            html.Td(d.get("holder_name", "—"), style={"fontSize": "12px"}),
            html.Td(_relative_time(ts), style={"fontSize": "11px", "color": "var(--text-muted)"}),
            html.Td(html.Button("⋮", className="btn-outline", style={"padding": "2px 8px"})),
        ]))

    return html.Div([
        html.Div("Analytics & User Tracking", className="page-title"),
        html.Div(style={"height": "20px"}),

        # Stat cards
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(4,1fr)", "gap": "14px", "marginBottom": "20px"},
            children=[
                html.Div(className="stat-card", children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                        html.Div("Total Active Nodes", className="stat-label"),
                        html.Span("((·))", style={"fontSize": "16px", "color": "var(--accent-light)"}),
                    ]),
                    html.Div(f"{total_nodes}", className="stat-value"),
                    html.Div("−12%", className="stat-delta down"),
                ]),
                html.Div(className="stat-card", children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                        html.Div("Data Throughput", className="stat-label"),
                        html.Span("⚡", style={"fontSize": "16px", "color": "var(--yellow)"}),
                    ]),
                    html.Div(f"{len(hourly_records) * 1.2:.1f} MB/s", className="stat-value"),
                    html.Div("−9.4%", className="stat-delta down"),
                ]),
                html.Div(className="stat-card", children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                        html.Div("System Latency", className="stat-label"),
                        html.Span("⏱", style={"fontSize": "16px", "color": "var(--yellow)"}),
                    ]),
                    html.Div("14ms", className="stat-value"),
                    html.Div("−2ms", className="stat-delta up"),
                ]),
                html.Div(className="stat-card", children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                        html.Div("Network Load", className="stat-label"),
                        html.Span("📡", style={"fontSize": "16px", "color": "var(--green)"}),
                    ]),
                    html.Div(f"{network_load}%", className="stat-value"),
                    html.Div("Stable", className="stat-delta up"),
                ]),
            ],
        ),

        # Charts — 3 columns
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "16px", "marginBottom": "20px"},
            children=[
                html.Div(className="cl-card", children=[
                    html.Div(className="section-header", children=[
                        html.Div("Hourly Records", className="section-title"),
                        html.Span("● Records", style={"fontSize": "11px", "color": "#9d5cf5"}),
                    ]),
                    html.Div("from /records/hourly-records",
                             style={"fontSize": "10px", "color": "var(--text-muted)", "marginBottom": "4px"}),
                    dcc.Graph(figure=trend_fig, config={"displayModeBar": False}),
                ]),
                html.Div(className="cl-card", children=[
                    html.Div(className="section-header", children=[
                        html.Div("Active Devices / Hour", className="section-title"),
                        html.Span("● Devices", style={"fontSize": "11px", "color": "#58a6ff"}),
                    ]),
                    html.Div("from /records/hourly-devices",
                             style={"fontSize": "10px", "color": "var(--text-muted)", "marginBottom": "4px"}),
                    dcc.Graph(figure=bar_fig, config={"displayModeBar": False}),
                ]),
                html.Div(className="cl-card", children=[
                    html.Div(className="section-header", children=[
                        html.Div("Avg Session Duration", className="section-title"),
                        html.Span("● Minutes", style={"fontSize": "11px", "color": "#3fb950"}),
                    ]),
                    html.Div("from /records/hourly-sessions-duration",
                             style={"fontSize": "10px", "color": "var(--text-muted)", "marginBottom": "4px"}),
                    dcc.Graph(figure=session_fig, config={"displayModeBar": False}),
                ]),
            ],
        ),

        # ── Room Analytics ────────────────────────────────────────────────────
        html.Div(style={"marginBottom": "20px"}, children=[
            html.Div("Room Analytics", className="page-title",
                     style={"fontSize": "15px", "marginBottom": "14px"}),

            # Two charts side by side
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                       "gap": "16px", "marginBottom": "16px"},
                children=[
                    html.Div(className="cl-card", children=[
                        html.Div(className="section-header", children=[
                            html.Div("Hourly Room Occupancy", className="section-title"),
                            html.Div("Unique patients per room per hour of day",
                                     style={"fontSize": "10px", "color": "var(--text-muted)"}),
                        ]),
                        dcc.Graph(figure=occupancy_fig, config={"displayModeBar": False}),
                    ]),
                    html.Div(className="cl-card", children=[
                        html.Div(className="section-header", children=[
                            html.Div("Room Dwell Time Ranking", className="section-title"),
                            html.Div("Average patient dwell time per room (highest first)",
                                     style={"fontSize": "10px", "color": "var(--text-muted)"}),
                        ]),
                        dcc.Graph(figure=dwell_fig, config={"displayModeBar": False}),
                    ]),
                ],
            ),

            # Patient-room breakdown table
            html.Div(className="cl-card", children=[
                html.Div(className="section-header", children=[
                    html.Div("Patient × Room Breakdown", className="section-title"),
                    html.Div("Time each patient spent in each room",
                             style={"fontSize": "11px", "color": "var(--text-muted)"}),
                ]),
                html.Table(
                    className="cl-table",
                    children=[
                        html.Thead(html.Tr([
                            html.Th("PATIENT"),
                            html.Th("ROOM"),
                            html.Th("VISITS"),
                            html.Th("TOTAL TIME"),
                            html.Th("AVG PER VISIT"),
                        ])),
                        html.Tbody([
                            html.Tr([
                                html.Td(r.get("patient_name", "—"), style={"fontWeight": 600}),
                                html.Td(r.get("router_name", "—")),
                                html.Td(str(r.get("visit_count", 0))),
                                html.Td(_fmt_seconds(r.get("total_seconds", 0))),
                                html.Td(_fmt_seconds(r.get("avg_seconds", 0)),
                                        style={"color": "var(--text-muted)"}),
                            ])
                            for r in patients_room_stats[:50]
                        ] or [html.Tr(html.Td("No data.", colSpan=5,
                                              style={"color": "var(--text-muted)",
                                                     "padding": "20px 14px"}))]),
                    ],
                ),
                html.Div(
                    f"Showing {min(50, len(patients_room_stats))} of {len(patients_room_stats)} rows",
                    style={"padding": "10px 14px", "fontSize": "11px",
                           "color": "var(--text-muted)"},
                ),
            ]),
        ]),

        # Tracked users table
        html.Div(className="cl-card", children=[
            html.Div(className="section-header", children=[
                html.Div([
                    html.Div("Tracked Active Users", className="section-title"),
                    html.Div("Real-time geolocation and device health",
                             style={"fontSize": "11px", "color": "var(--text-muted)"}),
                ]),
                html.Div(style={"display": "flex", "gap": "8px"}, children=[
                    html.Button("⊞ Filter", className="btn-outline", style={"fontSize": "12px", "padding": "5px 12px"}),
                    html.Button("↑ Export", className="btn-primary", style={"fontSize": "12px", "padding": "5px 12px"}),
                ]),
            ]),
            html.Table(
                className="cl-table",
                children=[
                    html.Thead(html.Tr([
                        html.Th("USER DETAILS"),
                        html.Th("LAST LOCATION"),
                        html.Th("STATUS"),
                        html.Th("DEVICE INFO"),
                        html.Th("LAST UPDATE"),
                        html.Th(""),
                    ])),
                    html.Tbody(device_rows if device_rows else [
                        html.Tr(html.Td("No data available.", colSpan=6,
                                        style={"color": "var(--text-muted)", "padding": "20px 14px"}))
                    ]),
                ],
            ),
            html.Div(
                style={"padding": "12px 14px", "fontSize": "12px", "color": "var(--text-muted)"},
                children=f"Showing 1–{min(20, len(devices))} of {len(devices)} users",
            ),
        ]),
    ])

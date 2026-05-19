import math
from datetime import datetime

import dash
from dash import dcc, html, callback, Input, Output, State
import plotly.graph_objects as go
import api
import floor_plan

dash.register_page(__name__, path="/", title="Dashboard — Central Link")

# ── Shared color helpers ───────────────────────────────────────────────────────

def _router_color(r, c, active_ids):
    if r.get("id") not in active_ids:
        return "#f85149"          # red   — offline
    return "#3fb950" if c > 0 else "#e3b341"  # green / amber


def _signal_label(r, c, active_ids):
    if r.get("id") not in active_ids:
        return "Offline"
    return f"Active · {c} device{'s' if c != 1 else ''}"


# ── Gaussian heat grid (pure Python, no numpy needed) ─────────────────────────

def _heat_grid(routers_map: list, N: int = 60):
    xs     = [i / (N - 1) for i in range(N)]
    ys     = [j / (N - 1) for j in range(N)]
    Z      = [[0.0] * N for _ in range(N)]
    sigma  = 0.14
    two_s2 = 2 * sigma * sigma

    for r in routers_map:
        rx = r.get("location_x", 0)
        ry = r.get("location_y", 0)
        c  = r.get("connected_devices_count", 0)
        if c <= 0:
            continue
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                Z[j][i] += c * math.exp(-((x - rx) ** 2 + (y - ry) ** 2) / two_s2)

    flat  = [v for row in Z for v in row]
    max_v = max(flat) if flat else 0
    if max_v > 0:
        Z = [[v / max_v for v in row] for row in Z]
    return xs, ys, Z, max_v > 0


_HEAT_CS = [
    [0.00, "rgba(0,0,0,0)"],
    [0.05, "rgba(31,111,235,0.40)"],
    [0.25, "rgba(31,111,235,0.65)"],
    [0.50, "rgba(63,185,80,0.75)"],
    [0.75, "rgba(243,133,38,0.85)"],
    [1.00, "rgba(248,81,73,0.95)"],
]

_FLOOR_LAYOUT = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=False,
    xaxis=dict(visible=False, range=[0, 1]),
    yaxis=dict(visible=False, range=[0, 1]),
    height=420,
)

# ── Figures ────────────────────────────────────────────────────────────────────

_DEVICE_RADIUS = 0.045   # orbit radius around each router (0–1 coord space)
_DEVICE_MAX    = 12      # cap displayed dots; router label still shows real count


def _add_device_dots(fig, routers_map, active_ids):
    """Draw one small dot per connected device, orbiting its router."""
    dot_xs, dot_ys, dot_colors = [], [], []

    for r in routers_map:
        count = r.get("connected_devices_count", 0)
        if count <= 0:
            continue
        rx    = r.get("location_x", 0)
        ry    = r.get("location_y", 0)
        color = "#3fb950" if r.get("id") in active_ids else "#f85149"
        n     = min(count, _DEVICE_MAX)
        for i in range(n):
            angle = 2 * math.pi * i / n - math.pi / 2   # start from top
            dot_xs.append(rx + _DEVICE_RADIUS * math.cos(angle))
            dot_ys.append(ry + _DEVICE_RADIUS * math.sin(angle))
            dot_colors.append(color)

    if dot_xs:
        fig.add_trace(go.Scatter(
            x=dot_xs, y=dot_ys,
            mode="markers",
            marker=dict(size=6, color=dot_colors,
                        line=dict(color="rgba(255,255,255,0.45)", width=1)),
            hoverinfo="skip",
        ))


def _add_room_labels(fig, routers_map):
    """Add room name + patient count below each router dot."""
    if not routers_map:
        return
    xs    = [r.get("location_x", 0) for r in routers_map]
    ys    = [r.get("location_y", 0) - 0.07 for r in routers_map]
    texts = [
        f"{r.get('name', r.get('id','')[:6])}<br>"
        f"<span style='color:#8b949e'>{r.get('connected_devices_count',0)} pts</span>"
        for r in routers_map
    ]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="text",
        text=texts,
        textfont=dict(size=8, color="#c9d1d9"),
        hoverinfo="skip",
    ))


def _add_router_markers(fig, routers_map, active_ids):
    if not routers_map:
        return
    xs     = [r.get("location_x", 0) for r in routers_map]
    ys     = [r.get("location_y", 0) for r in routers_map]
    counts = [r.get("connected_devices_count", 0) for r in routers_map]
    colors = [_router_color(r, c, active_ids) for r, c in zip(routers_map, counts)]
    names  = [r.get("id", "")[:8] for r in routers_map]
    labels = [
        f"Router {n}…<br>Devices: {c}<br>Signal: {_signal_label(r, c, active_ids)}"
        for n, c, r in zip(names, counts, routers_map)
    ]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        marker=dict(size=20, color=colors,
                    line=dict(color="rgba(255,255,255,0.5)", width=2)),
        text=[str(c) if c > 0 else "" for c in counts],
        textposition="middle center",
        textfont=dict(size=10, color="#fff"),
        customdata=labels,
        hovertemplate="%{customdata}<extra></extra>",
    ))


def make_floor_fig(routers_map: list, active_ids: set,
                   blueprint_url: str | None = None) -> go.Figure:
    fig = go.Figure()
    floor_plan.draw_clinic(fig)
    _add_device_dots(fig, routers_map, active_ids)
    _add_router_markers(fig, routers_map, active_ids)
    _add_room_labels(fig, routers_map)
    fig.update_layout(**_FLOOR_LAYOUT)
    return fig


def make_heatmap_fig(routers_map: list, active_ids: set) -> go.Figure:
    fig = go.Figure()
    floor_plan.draw_clinic(fig)

    if routers_map:
        xs_g, ys_g, Z, has_heat = _heat_grid(routers_map)

        if has_heat:
            fig.add_trace(go.Heatmap(
                x=xs_g, y=ys_g, z=Z,
                colorscale=_HEAT_CS,
                zmin=0, zmax=1,
                showscale=True,
                colorbar=dict(
                    title=dict(text="Load", font=dict(color="#8b949e", size=10)),
                    tickfont=dict(color="#8b949e", size=9),
                    tickvals=[0, 0.5, 1],
                    ticktext=["Low", "Mid", "High"],
                    thickness=12, x=1.01,
                ),
                hoverinfo="skip",
            ))

        _add_router_markers(fig, routers_map, active_ids)

    fig.update_layout(**_FLOOR_LAYOUT)
    return fig


# ── Stat card ──────────────────────────────────────────────────────────────────

def stat_card(label, value, sub="", icon="", delta_class="up"):
    return html.Div(className="stat-card", children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between",
                        "alignItems": "flex-start"},
                 children=[
                     html.Div(label, className="stat-label"),
                     html.Span(icon, style={"fontSize": "18px", "opacity": ".7"}),
                 ]),
        html.Div(value, className="stat-value"),
        html.Div(sub, className=f"stat-delta {delta_class}"),
    ])


# ── Layout ─────────────────────────────────────────────────────────────────────

def _fmt_visit_time(seconds: int) -> str:
    if seconds <= 0:  return "—"
    if seconds < 60:  return f"{seconds}s"
    if seconds < 3600: return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def layout():
    routers_map    = api.get_routers_map()
    routers        = api.get_routers()
    devices        = api.get_devices()
    blueprint_url  = api.get_blueprint()
    active_routers = api.get_active_routers()
    avg_visit      = api.get_avg_visit_time()

    active_ids    = {r["id"] for r in active_routers}
    total_routers = len(routers)
    active_count  = len(active_ids)
    total_devices = len(devices)
    network_load  = round((active_count / total_routers * 100) if total_routers else 0, 1)

    # Enrich routers_map with display names
    name_map = {r["id"]: r.get("name", r["id"][:8]) for r in routers}
    for r in routers_map:
        r["name"] = name_map.get(r.get("id", ""), r.get("id", "")[:8])

    # Busiest room right now
    busiest      = max(routers_map, key=lambda r: r.get("connected_devices_count", 0), default=None)
    busiest_name = busiest.get("name", "—") if busiest else "—"
    busiest_pts  = busiest.get("connected_devices_count", 0) if busiest else 0

    avg_visit_secs = int(avg_visit.get("avg_visit_seconds") or 0)
    avg_visit_str  = _fmt_visit_time(avg_visit_secs)
    avg_visit_sub  = f"across {avg_visit.get('patient_count', 0)} patient(s) today"

    floor_fig   = make_floor_fig(routers_map, active_ids, blueprint_url)
    heatmap_fig = make_heatmap_fig(routers_map, active_ids)

    return html.Div([
        dcc.Interval(id="dash-live-interval", interval=120_000, n_intervals=0),
        dcc.Store(id="floor-routers-data",  data=routers_map),
        dcc.Store(id="floor-blueprint-url", data=blueprint_url),
        dcc.Store(id="floor-zoom-state",    data=[0, 1, 0, 1]),
        dcc.Store(id="floor-active-ids",    data=list(active_ids)),
        dcc.Store(id="dash-active-tab",     data="floor"),

        html.Div(
            style={"display": "flex", "justifyContent": "space-between",
                   "alignItems": "center", "marginBottom": "24px"},
            children=[
                html.Div("DIGITAL TWIN — IoT & AI MONITORING",
                         style={"fontSize": "13px", "fontWeight": 700,
                                "letterSpacing": "1px", "color": "var(--text-muted)"}),
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "16px"}, children=[
                    html.Div(id="dash-last-updated",
                             style={"fontSize": "11px", "color": "var(--text-muted)"},
                             children=f"Last updated: {datetime.now().strftime('%H:%M:%S')}"),
                    html.Div(className="system-online", children=["System Online"]),
                ]),
            ],
        ),

        html.Div(
            id="dash-stats-row",
            style={"display": "grid", "gridTemplateColumns": "repeat(5, 1fr)",
                   "gap": "14px", "marginBottom": "24px"},
            children=[
                stat_card("Active Routers",   f"{active_count} / {total_routers}",
                          "Routers with recent signal", "⇌"),
                stat_card("Active Devices",    f"{total_devices}",
                          "BLE devices tracked", "((·))"),
                stat_card("Network Load",      f"{network_load}%",
                          "Based on active routers", "⚡", delta_class=""),
                stat_card("Avg Visit Time",    avg_visit_str,
                          avg_visit_sub, "⏱", delta_class=""),
                stat_card("Most Occupied Room", busiest_name,
                          f"{busiest_pts} patient{'s' if busiest_pts != 1 else ''} right now",
                          "📍", delta_class=""),
            ],
        ),

        html.Div(className="cl-card", children=[
            html.Div(className="section-header", children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "14px"}, children=[
                    html.Div([
                        html.Span("📍 ", style={"marginRight": "4px"}),
                        html.Span(id="card-section-title", className="section-title",
                                  children="Clinic Floor Plan"),
                    ]),
                    html.Div(style={"display": "flex", "gap": "6px"}, children=[
                        html.Button("Floor Plan", id="tab-btn-floor",
                                    className="btn-primary",
                                    style={"padding": "3px 12px", "fontSize": "11px"},
                                    n_clicks=0),
                        html.Button("Device Heatmap", id="tab-btn-heatmap",
                                    className="btn-outline",
                                    style={"padding": "3px 12px", "fontSize": "11px"},
                                    n_clicks=0),
                    ]),
                ]),
                html.Div(id="floor-controls", style={"display": "flex", "gap": "8px"}, children=[
                    html.Button("🔍+", id="floor-zoom-in",  className="btn-outline",
                                style={"padding": "4px 10px", "fontSize": "12px"}, n_clicks=0),
                    html.Button("🔍−", id="floor-zoom-out", className="btn-outline",
                                style={"padding": "4px 10px", "fontSize": "12px"}, n_clicks=0),
                    html.Button("⛶",  id="floor-fullscreen", className="btn-outline",
                                style={"padding": "4px 10px", "fontSize": "12px"}, n_clicks=0),
                ]),
            ]),

            # ── Floor plan tab ────────────────────────────────────────────
            html.Div(id="tab-content-floor", children=[
                html.Div(
                    id="floor-plan-wrap",
                    children=dcc.Graph(
                        id="floor-graph",
                        figure=floor_fig,
                        config={"displayModeBar": False},
                        style={"borderRadius": "8px", "overflow": "hidden"},
                    ),
                ),
                html.Div(
                    style={"display": "flex", "gap": "20px", "marginTop": "12px",
                           "flexWrap": "wrap"},
                    children=[
                        html.Div([html.Span("●", style={"color": "#3fb950", "marginRight": "6px"}),
                                  "Active · has devices"],
                                 style={"fontSize": "11px", "color": "var(--text-muted)"}),
                        html.Div([html.Span("●", style={"color": "#e3b341", "marginRight": "6px"}),
                                  "Active · no devices"],
                                 style={"fontSize": "11px", "color": "var(--text-muted)"}),
                        html.Div([html.Span("●", style={"color": "#f85149", "marginRight": "6px"}),
                                  "Offline (no recent signal)"],
                                 style={"fontSize": "11px", "color": "var(--text-muted)"}),
                    ],
                ),
            ]),

            # ── Heatmap tab ───────────────────────────────────────────────
            html.Div(id="tab-content-heatmap", style={"display": "none"}, children=[
                dcc.Graph(
                    id="heatmap-graph",
                    figure=heatmap_fig,
                    config={"displayModeBar": False},
                    style={"borderRadius": "8px", "overflow": "hidden"},
                ),
                html.Div(
                    style={"display": "flex", "gap": "20px", "marginTop": "12px",
                           "flexWrap": "wrap"},
                    children=[
                        html.Div("Heat intensity = connected device load at each router location.",
                                 style={"fontSize": "11px", "color": "var(--text-muted)"}),
                    ],
                ),
            ]),
        ]),
    ])


# ── Callbacks ──────────────────────────────────────────────────────────────────

ZOOM_STEP = 0.25


@callback(
    Output("tab-content-floor",   "style"),
    Output("tab-content-heatmap", "style"),
    Output("floor-controls",      "style"),
    Output("tab-btn-floor",       "className"),
    Output("tab-btn-heatmap",     "className"),
    Output("card-section-title",  "children"),
    Output("dash-active-tab",     "data"),
    Input("tab-btn-floor",   "n_clicks"),
    Input("tab-btn-heatmap", "n_clicks"),
    prevent_initial_call=True,
)
def switch_tab(n_floor, n_heatmap):
    if dash.ctx.triggered_id == "tab-btn-heatmap":
        return (
            {"display": "none"}, {},
            {"display": "none"},
            "btn-outline", "btn-primary",
            "Device Heatmap — Router Load",
            "heatmap",
        )
    return (
        {}, {"display": "none"},
        {"display": "flex", "gap": "8px"},
        "btn-primary", "btn-outline",
        "Clinic Floor Plan",
        "floor",
    )


@callback(
    Output("floor-zoom-state", "data"),
    Input("floor-zoom-in",  "n_clicks"),
    Input("floor-zoom-out", "n_clicks"),
    State("floor-zoom-state", "data"),
    prevent_initial_call=True,
)
def update_zoom(n_in, n_out, state):
    x0, x1, y0, y1 = state
    cx, cy   = (x0 + x1) / 2, (y0 + y1) / 2
    hw_x, hw_y = (x1 - x0) / 2, (y1 - y0) / 2
    if dash.ctx.triggered_id == "floor-zoom-in":
        hw_x = max(0.05, hw_x - ZOOM_STEP / 2)
        hw_y = max(0.05, hw_y - ZOOM_STEP / 2)
    else:
        hw_x = min(0.5, hw_x + ZOOM_STEP / 2)
        hw_y = min(0.5, hw_y + ZOOM_STEP / 2)
    return [max(0, cx - hw_x), min(1, cx + hw_x),
            max(0, cy - hw_y), min(1, cy + hw_y)]


@callback(
    Output("floor-graph", "figure"),
    Input("floor-zoom-state",   "data"),
    Input("floor-routers-data", "data"),
    State("floor-blueprint-url","data"),
    State("floor-active-ids",   "data"),
)
def apply_zoom(state, routers_map, blueprint_url, active_ids):
    x0, x1, y0, y1 = state
    fig = make_floor_fig(routers_map or [], set(active_ids or []), blueprint_url)
    fig.update_layout(
        xaxis=dict(visible=False, range=[x0, x1]),
        yaxis=dict(visible=False, range=[y0, y1]),
    )
    return fig


@callback(
    Output("heatmap-graph", "figure"),
    Input("floor-routers-data", "data"),
    State("floor-active-ids",   "data"),
)
def update_heatmap(routers_map, active_ids):
    return make_heatmap_fig(routers_map or [], set(active_ids or []))


@callback(
    Output("floor-plan-wrap", "style"),
    Input("floor-fullscreen", "n_clicks"),
    State("floor-plan-wrap",  "style"),
    prevent_initial_call=True,
)
def toggle_fullscreen(n, current_style):
    current_style = current_style or {}
    if current_style.get("position") == "fixed":
        return {}
    return {"position": "fixed", "top": "0", "left": "0",
            "width": "100vw", "height": "100vh", "zIndex": "500",
            "background": "#0d1117", "padding": "16px"}


@callback(
    Output("dash-stats-row",    "children"),
    Output("floor-routers-data","data"),
    Output("floor-active-ids",  "data"),
    Output("dash-last-updated", "children"),
    Input("dash-live-interval", "n_intervals"),
    prevent_initial_call=True,
)
def live_refresh(n):
    routers_map    = api.get_routers_map()
    routers        = api.get_routers()
    devices        = api.get_devices()
    active_routers = api.get_active_routers()
    avg_visit      = api.get_avg_visit_time()

    active_ids    = {r["id"] for r in active_routers}
    total_routers = len(routers)
    active_count  = len(active_ids)
    total_devices = len(devices)
    network_load  = round((active_count / total_routers * 100) if total_routers else 0, 1)

    name_map = {r["id"]: r.get("name", r["id"][:8]) for r in routers}
    for r in routers_map:
        r["name"] = name_map.get(r.get("id", ""), r.get("id", "")[:8])

    busiest      = max(routers_map, key=lambda r: r.get("connected_devices_count", 0), default=None)
    busiest_name = busiest.get("name", "—") if busiest else "—"
    busiest_pts  = busiest.get("connected_devices_count", 0) if busiest else 0

    avg_visit_secs = int(avg_visit.get("avg_visit_seconds") or 0)
    avg_visit_str  = _fmt_visit_time(avg_visit_secs)
    avg_visit_sub  = f"across {avg_visit.get('patient_count', 0)} patient(s) today"

    stats = [
        stat_card("Active Routers",    f"{active_count} / {total_routers}",
                  "Routers with recent signal", "⇌"),
        stat_card("Active Devices",    f"{total_devices}",
                  "BLE devices tracked", "((·))"),
        stat_card("Network Load",      f"{network_load}%",
                  "Based on active routers", "⚡", delta_class=""),
        stat_card("Avg Visit Time",    avg_visit_str,
                  avg_visit_sub, "⏱", delta_class=""),
        stat_card("Most Occupied Room", busiest_name,
                  f"{busiest_pts} patient{'s' if busiest_pts != 1 else ''} right now",
                  "📍", delta_class=""),
    ]
    ts = datetime.now().strftime("%H:%M:%S")
    return stats, routers_map, list(active_ids), f"Last updated: {ts}"

from datetime import datetime

import dash
from dash import dcc, html, callback, Input, Output, State
import plotly.graph_objects as go
import api
import floor_plan

dash.register_page(__name__, path="/", title="Dashboard — Central Link")


def make_floor_fig(routers_map: list, blueprint_url: str | None = None) -> go.Figure:
    fig = go.Figure()
    floor_plan.draw_clinic(fig)

    if routers_map:
        xs     = [r.get("location_x", 0) for r in routers_map]
        ys     = [r.get("location_y", 0) for r in routers_map]
        counts = [r.get("connected_devices_count", 0) for r in routers_map]
        colors = ["#3fb950" if c > 0 else "#f85149" for c in counts]
        names  = [r.get("id", "")[:8] for r in routers_map]
        labels = [f"Router {n}…<br>Devices: {c}" for n, c in zip(names, counts)]

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

    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        height=420,
    )
    return fig


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


def layout():
    routers_map   = api.get_routers_map()
    routers       = api.get_routers()
    devices       = api.get_devices()
    blueprint_url = api.get_blueprint()

    total_routers  = len(routers)
    active_routers = sum(1 for r in routers_map if r.get("connected_devices_count", 0) > 0)
    total_devices  = len(devices)
    network_load   = round((active_routers / total_routers * 100) if total_routers else 0, 1)

    floor_fig = make_floor_fig(routers_map, blueprint_url)

    return html.Div([
        dcc.Interval(id="dash-live-interval", interval=120_000, n_intervals=0),
        dcc.Store(id="floor-routers-data",  data=routers_map),
        dcc.Store(id="floor-blueprint-url", data=blueprint_url),
        dcc.Store(id="floor-zoom-state",    data=[0, 1, 0, 1]),

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
            style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)",
                   "gap": "16px", "marginBottom": "24px"},
            children=[
                stat_card("Active Routers", f"{active_routers} / {total_routers}",
                          "+2% since last hour", "⇌"),
                stat_card("Active Devices",  f"{total_devices}",
                          "+5% since last hour", "((·))"),
                stat_card("Network Load",    f"{network_load}%",
                          "Stable performance",  "⚡", delta_class=""),
            ],
        ),

        html.Div(className="cl-card", children=[
            html.Div(className="section-header", children=[
                html.Div([
                    html.Span("📍 ", style={"marginRight": "4px"}),
                    html.Span("Clinic Floor Plan", className="section-title"),
                ]),
                html.Div(style={"display": "flex", "gap": "8px"}, children=[
                    html.Button("🔍+", id="floor-zoom-in",  className="btn-outline",
                                style={"padding": "4px 10px", "fontSize": "12px"}, n_clicks=0),
                    html.Button("🔍−", id="floor-zoom-out", className="btn-outline",
                                style={"padding": "4px 10px", "fontSize": "12px"}, n_clicks=0),
                    html.Button("⛶",   id="floor-fullscreen", className="btn-outline",
                                style={"padding": "4px 10px", "fontSize": "12px"}, n_clicks=0),
                ]),
            ]),
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
                style={"display": "flex", "gap": "20px", "marginTop": "12px"},
                children=[
                    html.Div([html.Span("●", style={"color": "#3fb950", "marginRight": "6px"}),
                              "Active Router (number = devices)"],
                             style={"fontSize": "11px", "color": "var(--text-muted)"}),
                    html.Div([html.Span("●", style={"color": "#f85149", "marginRight": "6px"}),
                              "Offline Router"],
                             style={"fontSize": "11px", "color": "var(--text-muted)"}),
                ],
            ),
        ]),
    ])


ZOOM_STEP = 0.25


@callback(
    Output("floor-zoom-state", "data"),
    Input("floor-zoom-in",  "n_clicks"),
    Input("floor-zoom-out", "n_clicks"),
    State("floor-zoom-state", "data"),
    prevent_initial_call=True,
)
def update_zoom(n_in, n_out, state):
    x0, x1, y0, y1 = state
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
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
    Input("floor-zoom-state",    "data"),
    Input("floor-routers-data",  "data"),
    State("floor-blueprint-url", "data"),
)
def apply_zoom(state, routers_map, blueprint_url):
    x0, x1, y0, y1 = state
    fig = make_floor_fig(routers_map or [], blueprint_url)
    fig.update_layout(
        xaxis=dict(visible=False, range=[x0, x1]),
        yaxis=dict(visible=False, range=[y0, y1]),
    )
    return fig


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
    Output("dash-last-updated", "children"),
    Input("dash-live-interval", "n_intervals"),
    prevent_initial_call=True,
)
def live_refresh(n):
    routers_map    = api.get_routers_map()
    routers        = api.get_routers()
    devices        = api.get_devices()

    total_routers  = len(routers)
    active_routers = sum(1 for r in routers_map if r.get("connected_devices_count", 0) > 0)
    total_devices  = len(devices)
    network_load   = round((active_routers / total_routers * 100) if total_routers else 0, 1)

    stats = [
        stat_card("Active Routers", f"{active_routers} / {total_routers}",
                  "+2% since last hour", "⇌"),
        stat_card("Active Devices", f"{total_devices}",
                  "+5% since last hour", "((·))"),
        stat_card("Network Load",   f"{network_load}%",
                  "Stable performance",  "⚡", delta_class=""),
    ]
    ts = datetime.now().strftime("%H:%M:%S")
    return stats, routers_map, f"Last updated: {ts}"

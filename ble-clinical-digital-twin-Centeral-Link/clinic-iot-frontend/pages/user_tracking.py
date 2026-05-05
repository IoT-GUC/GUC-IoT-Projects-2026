from datetime import datetime, timezone
import os

import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import plotly.graph_objects as go
import api
import floor_plan

dash.register_page(__name__, path="/patients", title="Patient Tracking — Central Link")

ACTIVE_TIMEOUT = int(os.getenv("ACTIVE_TIMEOUT", 60))
IDLE_TIMEOUT   = int(os.getenv("IDLE_TIMEOUT", 300))

MODAL_HIDDEN  = {"display":"none","position":"fixed","top":0,"left":0,
                 "width":"100vw","height":"100vh",
                 "background":"rgba(0,0,0,.75)","zIndex":300,
                 "alignItems":"center","justifyContent":"center"}
MODAL_VISIBLE = {**MODAL_HIDDEN, "display":"flex"}


def _parse_ts(ts_str):
    ts_str = (ts_str or "").replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return None


def _relative_time(ts_str):
    dt = _parse_ts(str(ts_str or ""))
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    s = int((datetime.now(timezone.utc) - dt).total_seconds())
    if s < 60:    return f"{s}s ago"
    if s < 3600:  return f"{s//60}m ago"
    if s < 86400: return f"{s//3600}h ago"
    return f"{s//86400}d ago"


def _status_for_device(d):
    dt = _parse_ts(str(d.get("last_record_timestamp") or ""))
    if not dt:
        return "Offline", "badge-offline"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = (datetime.now(timezone.utc) - dt).total_seconds()
    if diff < ACTIVE_TIMEOUT:  return "Active", "badge-active"
    if diff < IDLE_TIMEOUT: return "Idle",   "badge-idle"
    return "Offline", "badge-offline"


def _avg_session_str(hourly_sessions):
    if not hourly_sessions:
        return "—"
    last = str(hourly_sessions[-1].get("average_total_session_duration") or "")
    if "T" in last:
        last = last.split("T")[-1]
    parts = last.replace("Z","").split(":")
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(float(parts[2]))
        return f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"
    except Exception:
        return last[:8] or "—"


def make_cluster_map(routers_map, blueprint_url=None):
    fig = go.Figure()
    floor_plan.draw_clinic(fig)

    if routers_map:
        xs     = [r.get("location_x", 0) for r in routers_map]
        ys     = [r.get("location_y", 0) for r in routers_map]
        counts = [r.get("connected_devices_count", 0) for r in routers_map]
        sizes  = [min(28, max(14, c * 2 + 14)) for c in counts]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            marker=dict(size=sizes, color="rgba(88,166,255,0.55)",
                        line=dict(color="#58a6ff", width=2)),
            text=[f"{c} device{'s' if c!=1 else ''}" for c in counts],
            hoverinfo="text",
        ))
    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        margin=dict(l=0,r=0,t=0,b=0), showlegend=False,
        xaxis=dict(visible=False, range=[0,1]),
        yaxis=dict(visible=False, range=[0,1]),
        height=260,
    )
    return fig


def build_rows(devices, router_filter="all"):
    rows = []
    for d in devices[:50]:
        if router_filter != "all" and d.get("router_id") != router_filter:
            continue
        label, badge = _status_for_device(d)
        initial = (d.get("name") or "?")[0].upper()
        did = d.get("id", "")
        rows.append(html.Tr([
            html.Td(html.Div(style={"display":"flex","alignItems":"center","gap":"10px"}, children=[
                html.Div(initial, style={
                    "width":"32px","height":"32px","borderRadius":"50%",
                    "background":"linear-gradient(135deg,#6e40c9,#1f6feb)",
                    "display":"flex","alignItems":"center","justifyContent":"center",
                    "fontSize":"12px","fontWeight":700,"color":"#fff","flexShrink":0,
                }),
                html.Div([
                    html.Div(d.get("name","—"), style={"fontWeight":600,"fontSize":"13px"}),
                    html.Div(did[:18], style={"fontSize":"11px","color":"var(--text-muted)"}),
                ]),
            ])),
            html.Td(d.get("router_name","—"), style={"fontSize":"12px"}),
            html.Td(d.get("holder_name","—"), style={"fontSize":"12px"}),
            html.Td(html.Span(label, className=badge)),
            html.Td(_relative_time(str(d.get("last_record_timestamp") or "")),
                    style={"fontSize":"11px","color":"var(--text-muted)"}),
            html.Td(html.Div(style={"display":"flex","gap":"6px"}, children=[
                html.Button("⋮", className="btn-outline",
                            id={"type":"device-menu-btn","index":did},
                            n_clicks=0, style={"padding":"2px 8px"}),
                html.Button("Release", className="btn-danger",
                            id={"type":"release-btn","index":did},
                            n_clicks=0,
                            style={"fontSize":"11px","padding":"3px 8px",
                                   "display":"" if d.get("holder_name") else "none"}),
            ])),
        ]))
    return rows or [html.Tr(html.Td("No devices found.", colSpan=6,
                                    style={"color":"var(--text-muted)","padding":"20px 14px"}))]


def layout():
    routers_map     = api.get_routers_map()
    devices         = api.get_devices_with_info()
    routers         = api.get_routers()
    hourly_sessions = api.get_hourly_sessions_duration()
    blueprint_url   = api.get_blueprint()

    # Merge patient_id from basic /devices (not included in with-routers-info)
    basic_devices = api.get_devices()
    pid_map = {d["id"]: d.get("patient_id") for d in basic_devices}
    for d in devices:
        d["patient_id"] = pid_map.get(d.get("id"))

    total_users  = len(devices)
    avg_session  = _avg_session_str(hourly_sessions)
    cluster_fig  = make_cluster_map(routers_map, blueprint_url)

    free_devices = [d for d in basic_devices if not d.get("patient_id")]
    device_options = [{"label": f"{d.get('name','?')} ({d['id'][:8]})", "value": d["id"]}
                      for d in free_devices]

    router_options = [{"label":"All Routers","value":"all"}] + [
        {"label": r.get("name", r["id"]), "value": r["id"]} for r in routers
    ]

    return html.Div([
        dcc.Store(id="ut-devices-data",    data=devices),
        dcc.Store(id="ut-map-data",        data=routers_map),
        dcc.Store(id="ut-blueprint-url",   data=blueprint_url),
        dcc.Store(id="ut-free-devices",    data=free_devices),

        html.Div(style={"display":"flex","gap":"12px","alignItems":"center","marginBottom":"24px"}, children=[
            dcc.Input(id="user-search", type="text", debounce=True,
                      placeholder="🔍  Search patients ...",
                      className="cl-input", style={"flex":1}),
            html.Button("+ Add Patient", id="open-add-user", className="btn-primary", n_clicks=0),
        ]),

        html.Div("Patient Tracking & Activity", className="page-title"),
        html.Div(style={"height":"16px"}),

        html.Div(
            style={"display":"grid","gridTemplateColumns":"repeat(3,1fr)","gap":"14px","marginBottom":"20px"},
            children=[
                html.Div(className="stat-card", children=[
                    html.Div(style={"display":"flex","justifyContent":"space-between"}, children=[
                        html.Div("Total Active Devices", className="stat-label"),
                        html.Span("👥", style={"fontSize":"18px"}),
                    ]),
                    html.Div(f"{total_users:,}", className="stat-value"),
                    html.Div("from /devices/with-routers-info",
                             style={"fontSize":"10px","color":"var(--text-muted)"}),
                ]),
                html.Div(className="stat-card", children=[
                    html.Div(style={"display":"flex","justifyContent":"space-between"}, children=[
                        html.Div("Avg. Session Time", className="stat-label"),
                        html.Span("⏱", style={"fontSize":"18px"}),
                    ]),
                    html.Div(avg_session, className="stat-value"),
                    html.Div("from /records/hourly-sessions-duration",
                             style={"fontSize":"10px","color":"var(--text-muted)"}),
                ]),
                html.Div(className="stat-card", children=[
                    html.Div(style={"display":"flex","justifyContent":"space-between"}, children=[
                        html.Div("Free Devices", className="stat-label"),
                        html.Span("🔓", style={"fontSize":"18px"}),
                    ]),
                    html.Div(f"{len(free_devices)}", className="stat-value"),
                    html.Div("unassigned devices", style={"fontSize":"10px","color":"var(--text-muted)"}),
                ]),
            ],
        ),

        html.Div(className="cl-card", style={"marginBottom":"20px"}, children=[
            html.Div(className="section-header", children=[
                html.Div([
                    html.Span("▦ "),
                    html.Span("Live Map — Device Clusters", className="section-title"),
                ]),
                html.Div(style={"display":"flex","gap":"8px"}, children=[
                    html.Button("Real-time",   id="map-realtime", n_clicks=0,
                                className="btn-primary",
                                style={"fontSize":"11px","padding":"4px 12px"}),
                    html.Button("24h History", id="map-history",  n_clicks=0,
                                className="btn-outline",
                                style={"fontSize":"11px","padding":"4px 12px"}),
                ]),
            ]),
            dcc.Graph(id="cluster-map-graph", figure=cluster_fig,
                      config={"displayModeBar":False}),
            html.Div(style={"display":"flex","gap":"16px","marginTop":"8px"}, children=[
                html.Div([html.Span("●", style={"color":"#58a6ff","marginRight":"5px"}),
                          "Router (size = device count)"],
                         style={"fontSize":"11px","color":"var(--text-muted)"}),
            ]),
        ]),

        html.Div(className="cl-card", children=[
            html.Div(className="section-header", children=[
                html.Div("Active Sessions", className="section-title"),
                dcc.Dropdown(id="session-router-filter", options=router_options,
                             value="all", clearable=False,
                             style={"width":"160px","fontSize":"12px"}),
            ]),
            html.Div(id="release-msg", style={"marginBottom":"8px"}),
            html.Div(id="sessions-table-wrap", children=html.Table(
                className="cl-table",
                children=[
                    html.Thead(html.Tr([
                        html.Th("DEVICE"), html.Th("CONNECTED ROUTER"),
                        html.Th("PATIENT (HOLDER)"), html.Th("STATUS"),
                        html.Th("LAST UPDATE"), html.Th("ACTIONS"),
                    ])),
                    html.Tbody(build_rows(devices)),
                ],
            )),
            html.Div(f"Showing {min(50,total_users)} of {total_users} — from /devices/with-routers-info",
                     style={"padding":"12px 14px","fontSize":"11px","color":"var(--text-muted)"}),
        ]),

        # Device detail modal
        html.Div(id="device-modal-backdrop", style={**MODAL_HIDDEN},
            children=[html.Div(className="cl-card",
                style={"width":"540px","maxHeight":"85vh","overflowY":"auto"},
                children=[
                    html.Div(style={"display":"flex","justifyContent":"space-between",
                                    "alignItems":"center","marginBottom":"20px"}, children=[
                        html.Div(id="device-modal-title",
                                 style={"fontSize":"18px","fontWeight":700}),
                        html.Button("✕", id="close-device-modal", n_clicks=0,
                                    className="btn-outline",
                                    style={"padding":"2px 10px","fontSize":"16px"}),
                    ]),
                    html.Div(id="device-modal-body"),
                ],
            )],
        ),

        # Add Patient modal
        html.Div(id="add-user-backdrop",
            style={"display":"none","position":"fixed","top":0,"left":0,
                   "width":"100vw","height":"100vh",
                   "background":"rgba(0,0,0,.75)","zIndex":300,
                   "alignItems":"center","justifyContent":"center"},
            children=[html.Div(className="cl-card", style={"width":"420px"},
                children=[
                    html.Div(style={"display":"flex","justifyContent":"space-between",
                                    "alignItems":"center","marginBottom":"16px"}, children=[
                        html.Div("Add Patient", style={"fontSize":"18px","fontWeight":700}),
                        html.Button("✕", id="close-add-user", n_clicks=0,
                                    className="btn-outline",
                                    style={"padding":"2px 10px","fontSize":"16px"}),
                    ]),
                    html.Div("Assign a BLE device to a new patient",
                             style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
                    html.Div("PATIENT NAME", className="cl-label"),
                    dcc.Input(id="new-user-name", type="text", placeholder="Patient Name",
                              className="cl-input", style={"marginBottom":"16px"}),
                    html.Div("ASSIGN DEVICE", className="cl-label"),
                    dcc.Dropdown(id="new-patient-device",
                                 options=device_options,
                                 placeholder="Select a free device...",
                                 clearable=False,
                                 style={"marginBottom":"20px","fontSize":"13px"}),
                    html.Div(id="add-user-msg"),
                    html.Button("Add Patient", id="add-user-btn", n_clicks=0,
                                className="btn-primary", style={"width":"100%"}),
                ],
            )],
        ),
    ])


@callback(
    Output("add-user-backdrop", "style"),
    Input("open-add-user",  "n_clicks"),
    Input("close-add-user", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_patient_modal(open_n, close_n):
    return MODAL_VISIBLE if ctx.triggered_id == "open-add-user" else MODAL_HIDDEN


@callback(
    Output("add-user-msg", "children"),
    Input("add-user-btn",  "n_clicks"),
    State("new-user-name",      "value"),
    State("new-patient-device", "value"),
    prevent_initial_call=True,
)
def add_patient(n, name, device_id):
    if not name or not device_id:
        return html.Div("Patient name and device are required.", className="alert-error",
                        style={"marginBottom":"8px"})
    result, err = api.create_patient(name, device_id)
    if result is None:
        return html.Div(err or "Failed to add patient — check connection.", className="alert-error",
                        style={"marginBottom":"8px"})
    return html.Div(f"Patient '{name}' added successfully.", className="alert-success",
                    style={"marginBottom":"8px"})


@callback(
    Output("release-msg",         "children"),
    Output("sessions-table-wrap", "children", allow_duplicate=True),
    Input({"type":"release-btn","index":dash.ALL}, "n_clicks"),
    State("ut-devices-data", "data"),
    prevent_initial_call=True,
)
def release_device(release_clicks, devices):
    triggered = ctx.triggered_id
    if not triggered or not any(release_clicks or []):
        return dash.no_update, dash.no_update
    did = triggered["index"]
    ok  = api.release_device(did)
    if ok:
        # Refresh the device list
        updated = api.get_devices_with_info()
        rows    = build_rows(updated)
        table   = html.Table(className="cl-table", children=[
            html.Thead(html.Tr([
                html.Th("DEVICE"), html.Th("CONNECTED ROUTER"),
                html.Th("PATIENT (HOLDER)"), html.Th("STATUS"),
                html.Th("LAST UPDATE"), html.Th("ACTIONS"),
            ])),
            html.Tbody(rows),
        ])
        return html.Div("Device released successfully.", className="alert-success",
                        style={"marginBottom":"8px"}), table
    return html.Div("Failed to release device.", className="alert-error",
                    style={"marginBottom":"8px"}), dash.no_update


@callback(
    Output("cluster-map-graph", "figure"),
    Output("map-realtime", "className"),
    Output("map-history",  "className"),
    Input("map-realtime",  "n_clicks"),
    Input("map-history",   "n_clicks"),
    State("ut-map-data",       "data"),
    State("ut-blueprint-url",  "data"),
    prevent_initial_call=True,
)
def toggle_map_mode(rt_n, hist_n, routers_map, blueprint_url):
    is_realtime = ctx.triggered_id == "map-realtime"
    fig = make_cluster_map(routers_map or [] if is_realtime else [], blueprint_url)
    if not is_realtime:
        fig.add_trace(go.Scatter(
            x=[r.get("location_x",0) for r in (routers_map or [])],
            y=[r.get("location_y",0) for r in (routers_map or [])],
            mode="markers",
            marker=dict(size=16, color="rgba(139,148,158,0.5)",
                        line=dict(color="#8b949e", width=1.5)),
            hoverinfo="skip",
        ))
    return fig, ("btn-primary" if is_realtime else "btn-outline"), ("btn-outline" if is_realtime else "btn-primary")


@callback(
    Output("device-modal-backdrop", "style"),
    Output("device-modal-title",    "children"),
    Output("device-modal-body",     "children"),
    Output("url",                   "pathname", allow_duplicate=True),
    Input({"type":"device-menu-btn","index":dash.ALL}, "n_clicks"),
    Input("close-device-modal", "n_clicks"),
    State("ut-devices-data", "data"),
    prevent_initial_call=True,
)
def device_modal(menu_clicks, close_n, devices):
    triggered = ctx.triggered_id
    if triggered == "close-device-modal":
        return MODAL_HIDDEN, "", [], dash.no_update
    if not triggered or not any(menu_clicks or []):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    did    = triggered["index"]
    device = next((d for d in (devices or []) if d.get("id") == did), None)
    if not device:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    label, badge = _status_for_device(device)
    holder = device.get("holder_name")
    pid    = device.get("patient_id")

    # Fetch patient sessions if assigned
    sessions = api.get_patient_sessions(pid) if pid else []

    # Build sessions chart
    if sessions:
        durations = [round((s.get("duration") or 0) / 60, 1) for s in sessions]
        routers   = [s.get("router_name", "—") for s in sessions]

        sess_fig = go.Figure()
        sess_fig.add_trace(go.Bar(
            x=routers, y=durations,
            marker_color="#1f6feb",
            customdata=routers,
            hovertemplate="<b>%{x}</b><br>%{y:.1f} min · %{customdata}<extra></extra>",
        ))
        sess_fig.update_layout(
            paper_bgcolor="#1c2230", plot_bgcolor="#1c2230",
            font=dict(color="#8b949e", size=9),
            margin=dict(l=36, r=12, t=8, b=36),
            showlegend=False, bargap=0.3, height=180,
            xaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=8)),
            yaxis=dict(gridcolor="#21262d", zeroline=False,
                       tickfont=dict(size=8), title="min"),
        )
        sessions_block = html.Div([
            html.Div("Patient Sessions", className="section-title",
                     style={"marginTop":"20px","marginBottom":"6px"}),
            html.Div(f"{len(sessions)} session(s) recorded",
                     style={"fontSize":"11px","color":"var(--text-muted)","marginBottom":"4px"}),
            dcc.Graph(figure=sess_fig, config={"displayModeBar": False}),
        ])
    else:
        sessions_block = html.Div(
            "No sessions recorded yet." if pid else "No patient assigned to this device.",
            style={"marginTop":"16px","fontSize":"12px","color":"var(--text-muted)"},
        )

    body = html.Div([
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"12px",
                        "marginBottom":"20px"}, children=[
            html.Div(className="stat-card", style={"padding":"12px"}, children=[
                html.Div("STATUS", className="stat-label"),
                html.Span(label, className=badge,
                          style={"marginTop":"8px","display":"inline-block"}),
            ]),
            html.Div(className="stat-card", style={"padding":"12px"}, children=[
                html.Div("ROUTER", className="stat-label"),
                html.Div(device.get("router_name","—"),
                         style={"fontWeight":600,"marginTop":"6px","fontSize":"13px"}),
            ]),
            html.Div(className="stat-card", style={"padding":"12px"}, children=[
                html.Div("PATIENT", className="stat-label"),
                html.Div(holder or "Unassigned",
                         style={"fontWeight":600,"marginTop":"6px","fontSize":"13px",
                                "color":"var(--text-primary)" if holder else "var(--text-muted)"}),
            ]),
            html.Div(className="stat-card", style={"padding":"12px"}, children=[
                html.Div("LAST SEEN", className="stat-label"),
                html.Div(str(device.get("last_record_timestamp") or "—")[:16],
                         style={"fontWeight":600,"marginTop":"6px","fontSize":"12px"}),
            ]),
        ]),
        html.Div("DEVICE ID", className="cl-label"),
        html.Div(did, style={"fontFamily":"monospace","fontSize":"12px",
                              "color":"var(--text-muted)","marginTop":"4px","wordBreak":"break-all"}),
        sessions_block,
    ])
    return MODAL_VISIBLE, device.get("name", did), body, dash.no_update


@callback(
    Output("sessions-table-wrap", "children"),
    Input("session-router-filter", "value"),
    State("ut-devices-data", "data"),
    prevent_initial_call=True,
)
def filter_sessions(router_id, devices):
    rows = build_rows(devices or [], router_id or "all")
    return html.Table(className="cl-table", children=[
        html.Thead(html.Tr([
            html.Th("DEVICE"), html.Th("CONNECTED ROUTER"),
            html.Th("PATIENT (HOLDER)"), html.Th("STATUS"),
            html.Th("LAST UPDATE"), html.Th("ACTIONS"),
        ])),
        html.Tbody(rows),
    ])

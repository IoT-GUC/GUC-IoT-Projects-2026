import re

import dash
from dash import dcc, html, callback, clientside_callback, ClientsideFunction, Input, Output, State, ctx
import api

dash.register_page(__name__, path="/devices", title="Device Management — Central Link")


def device_card(device: dict) -> html.Div:
    did     = device["id"]
    name    = device.get("name", "Unknown")
    pid     = device.get("patient_id")
    assigned = pid is not None
    badge_cls = "badge-active" if assigned else "badge-idle"
    badge_lbl = "ASSIGNED" if assigned else "FREE"

    return html.Div(className="router-card", children=[
        html.Div(badge_lbl, className=f"router-card-status {badge_cls}"),
        html.Div("◉", style={"fontSize":"22px","color":"var(--accent-light)"}),
        html.Div(name, className="router-card-name"),
        html.Div(did[:20], className="router-card-loc",
                 style={"fontFamily":"monospace","fontSize":"10px"}),
        html.Div(className="router-card-meta", children=[
            html.Div([html.Div("STATUS",  className="router-card-meta-item"),
                      html.Div("In Use" if assigned else "Available", className="router-card-meta-val")]),
            html.Div([html.Div("PATIENT", className="router-card-meta-item"),
                      html.Div(str(pid)[:8] if pid else "—", className="router-card-meta-val")]),
        ]),
        html.Div(style={"display":"flex","gap":"8px"}, children=[
            html.Button("Release", n_clicks=0,
                        id={"type":"dm-release-btn","index":did},
                        className="btn-outline",
                        style={"flex":1,"fontSize":"12px",
                               "display":"" if assigned else "none"}),
            html.Button("⋮", n_clicks=0,
                        id={"type":"dm-info-btn","index":did},
                        className="btn-outline", style={"fontSize":"12px"}),
        ]),
    ])


def build_cards(devices, filter_val="all", search=""):
    cards = []
    for d in devices:
        assigned = d.get("patient_id") is not None
        status   = "assigned" if assigned else "free"
        if filter_val not in ("all", status):
            continue
        if search and search.lower() not in d.get("name","").lower():
            continue
        cards.append(device_card(d))
    return cards or [html.Div("No devices match this filter.",
                               style={"color":"var(--text-muted)","padding":"20px 0"})]


def layout():
    devices     = api.get_devices()
    assigned    = sum(1 for d in devices if d.get("patient_id") is not None)
    free        = len(devices) - assigned

    return html.Div([
        dcc.Store(id="dm-devices-data",   data=devices),
        dcc.Store(id="dm-selected",       data=None),
        dcc.Store(id="dm-serial-result",  data=None),
        dcc.Store(id="dm-edit-device-id", data=None),

        html.Div(style={"display":"flex","gap":"12px","alignItems":"center","marginBottom":"24px"}, children=[
            dcc.Input(id="device-search", type="text", debounce=True,
                      placeholder="🔍  Search devices...",
                      className="cl-input", style={"flex":1}),
            html.Button("+ Add Device", id="open-add-device",
                        className="btn-primary", n_clicks=0),
        ]),

        html.Div(style={"display":"flex","gap":"24px"}, children=[
            html.Div(style={"flex":1}, children=[
                html.Div(style={"display":"flex","justifyContent":"space-between",
                                "alignItems":"flex-start","marginBottom":"20px"}, children=[
                    html.Div([
                        html.Div("Device Management", className="page-title"),
                        html.Div("Manage BLE devices in your clinic network.",
                                 className="page-sub", style={"marginBottom":0}),
                    ]),
                    html.Div(style={"display":"flex","gap":"10px"}, children=[
                        html.Div(className="cl-card",
                                 style={"padding":"10px 18px","textAlign":"center"}, children=[
                            html.Span("FREE", style={"fontSize":"9px","color":"var(--text-muted)","display":"block"}),
                            html.Span(str(free), style={"fontSize":"20px","fontWeight":700,"color":"var(--green)"}),
                        ]),
                        html.Div(className="cl-card",
                                 style={"padding":"10px 18px","textAlign":"center"}, children=[
                            html.Span("ASSIGNED", style={"fontSize":"9px","color":"var(--text-muted)","display":"block"}),
                            html.Span(str(assigned), style={"fontSize":"20px","fontWeight":700,"color":"var(--yellow)"}),
                        ]),
                    ]),
                ]),

                html.Div(style={"display":"flex","gap":"8px","marginBottom":"20px"}, children=[
                    html.Button("All Devices", id="df-all",      n_clicks=0, className="btn-primary",
                                style={"fontSize":"12px","padding":"5px 14px"}),
                    html.Button("Free",        id="df-free",     n_clicks=0, className="btn-outline",
                                style={"fontSize":"12px","padding":"5px 14px"}),
                    html.Button("Assigned",    id="df-assigned", n_clicks=0, className="btn-outline",
                                style={"fontSize":"12px","padding":"5px 14px"}),
                ]),

                html.Div(id="device-release-msg", style={"marginBottom":"8px"}),

                html.Div(id="device-cards-grid",
                         style={"display":"grid",
                                "gridTemplateColumns":"repeat(auto-fill, minmax(220px, 1fr))",
                                "gap":"16px"},
                         children=build_cards(devices)),
            ]),

            # Edit Device panel (rename)
            html.Div(id="edit-device-panel",
                     style={"display":"none","width":"300px","flexShrink":0}, children=[
                html.Div(className="cl-card", children=[
                    html.Div(style={"display":"flex","justifyContent":"space-between",
                                    "alignItems":"center","marginBottom":"4px"}, children=[
                        html.Div("Edit Device",
                                 style={"fontSize":"18px","fontWeight":700}),
                        html.Button("✕", id="close-edit-device", n_clicks=0,
                                    className="btn-outline",
                                    style={"padding":"2px 10px","fontSize":"14px"}),
                    ]),
                    html.Div("Rename this BLE device",
                             style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
                    html.Div("DEVICE NAME", className="cl-label"),
                    dcc.Input(id="dm-edit-name", type="text", placeholder="Device Name",
                              className="cl-input", style={"marginBottom":"8px"}),
                    html.Div(id="dm-edit-msg", style={"marginBottom":"8px"}),
                    html.Button("Save Name", id="dm-save-name-btn", n_clicks=0,
                                className="btn-primary", style={"width":"100%"}),
                ]),
            ]),

            # Add Device panel
            html.Div(id="add-device-panel",
                     style={"display":"none","width":"300px","flexShrink":0}, children=[
                html.Div(className="cl-card", children=[
                    html.Div("Add Device",
                             style={"fontSize":"18px","fontWeight":700,"marginBottom":"4px"}),
                    html.Div("Register a new BLE device",
                             style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),

                    html.Div(
                        style={"display":"flex","justifyContent":"space-between",
                               "alignItems":"center","marginBottom":"6px"},
                        children=[
                            html.Div("DEVICE ID (MAC Address)", className="cl-label",
                                     style={"marginBottom":0}),
                            html.Div(style={"display":"flex","gap":"6px"}, children=[
                                html.Button("⟳ Scan", id="scan-device-btn", n_clicks=0,
                                            className="btn-outline",
                                            style={"fontSize":"10px","padding":"3px 10px"}),
                                html.Button("✕ Stop", id="stop-scan-btn", n_clicks=0,
                                            className="btn-outline",
                                            style={"fontSize":"10px","padding":"3px 10px",
                                                   "color":"#f85149","display":"none"}),
                            ]),
                        ]
                    ),
                    html.Div(
                        style={"position":"relative","marginBottom":"4px"},
                        children=[
                            dcc.Input(id="new-device-id", type="text",
                                      className="cl-input",
                                      placeholder="XX:XX:XX:XX:XX:XX",
                                      style={"fontFamily":"monospace","fontSize":"11px",
                                             "color":"var(--accent-light)","opacity":1,
                                             "cursor":"text"}),
                        ],
                    ),
                    html.Div(id="dm-scan-status",
                             style={"fontSize":"10px","minHeight":"16px",
                                    "marginBottom":"16px"}),

                    html.Div("DEVICE NAME", className="cl-label"),
                    dcc.Input(id="new-device-name", type="text", placeholder="Device Name",
                              className="cl-input", style={"marginBottom":"20px"}),
                    html.Div(id="add-device-msg"),
                    html.Button("Add Device", id="add-device-btn", n_clicks=0,
                                className="btn-primary", style={"width":"100%"}),
                ]),
            ]),
        ]),
    ])


@callback(
    Output("add-device-panel", "style"),
    Input("open-add-device",  "n_clicks"),
    State("add-device-panel", "style"),
    prevent_initial_call=True,
)
def toggle_add_panel(n, style):
    return {**style, "display":"block" if style.get("display")=="none" else "none"}


@callback(
    Output("add-device-msg",        "children"),
    Output("device-cards-grid",     "children", allow_duplicate=True),
    Output("new-device-id", "value"),
    Output("new-device-name",  "value"),
    Output("dm-devices-data",  "data"),
    Input("add-device-btn",   "n_clicks"),
    State("new-device-id", "value"),
    State("new-device-name",  "value"),
    State("dm-devices-data",  "data"),
    prevent_initial_call=True,
)
def add_device(_, did, name, devices):
    no_updates = (dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    if not did or not re.fullmatch(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", did):
        return (html.Div("Device ID is not valid.", className="alert-error",
                         style={"marginBottom":"8px"}),
                *no_updates)
    if not name:
        return (html.Div("Device name is required.", className="alert-error",
                         style={"marginBottom":"8px"}),
                *no_updates)
    result, err = api.create_device(did, name)
    if result is None:
        return (html.Div(err or "Failed to create device — check connection.",
                         className="alert-error", style={"marginBottom":"8px"}),
                *no_updates)
    new_entry = {"id": did, "name": name, "patient_id": None}
    updated   = (devices or []) + [new_entry]
    return (html.Div(f"'{name}' added.", className="alert-success",
                     style={"marginBottom":"8px"}),
            build_cards(updated),
            '',
            '',
            updated,
            )

@callback(
    Output("device-release-msg", "children"),
    Output("dm-devices-data",    "data",     allow_duplicate=True),
    Output("device-cards-grid",  "children", allow_duplicate=True),
    Input({"type":"dm-release-btn","index":dash.ALL}, "n_clicks"),
    State("dm-devices-data", "data"),
    prevent_initial_call=True,
)
def release_device(release_clicks, devices):
    triggered = ctx.triggered_id
    if not triggered or not any(release_clicks or []):
        return dash.no_update, dash.no_update, dash.no_update
    did = triggered["index"]
    ok  = api.release_device(did)
    if ok:
        updated = api.get_devices()
        return (html.Div("Device released.", className="alert-success",
                         style={"marginBottom":"8px"}),
                updated, build_cards(updated))
    return (html.Div("Failed to release device.", className="alert-error",
                     style={"marginBottom":"8px"}),
            dash.no_update, dash.no_update)


clientside_callback(
    ClientsideFunction(namespace="serial", function_name="scan_device"),
    Output("new-device-id",  "value",    allow_duplicate=True),
    Output("dm-scan-status", "children", allow_duplicate=True),
    Input("scan-device-btn", "n_clicks"),
    prevent_initial_call=True,
)


clientside_callback(
    ClientsideFunction(namespace="serial", function_name="stop_scan"),
    Output("dm-scan-status", "children", allow_duplicate=True),
    Input("stop-scan-btn",   "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("device-cards-grid", "children"),
    Output("df-all",      "className"),
    Output("df-free",     "className"),
    Output("df-assigned", "className"),
    Input("df-all",       "n_clicks"),
    Input("df-free",      "n_clicks"),
    Input("df-assigned",  "n_clicks"),
    Input("device-search","value"),
    State("dm-devices-data","data"),
    prevent_initial_call=True,
)
def filter_cards(n_all, n_free, n_assigned, search, devices):
    tid    = ctx.triggered_id or "df-all"
    fmap   = {"df-all":"all","df-free":"free","df-assigned":"assigned"}
    active = fmap.get(tid,"all") if tid in fmap else "all"
    cards  = build_cards(devices or [], active, search or "")
    cls    = lambda k: "btn-primary" if active==k else "btn-outline"
    return cards, cls("all"), cls("free"), cls("assigned")


@callback(
    Output("edit-device-panel",  "style"),
    Output("dm-edit-name",       "value"),
    Output("dm-edit-device-id",  "data"),
    Input({"type":"dm-info-btn","index":dash.ALL}, "n_clicks"),
    Input("close-edit-device",   "n_clicks"),
    State("dm-devices-data",     "data"),
    prevent_initial_call=True,
)
def toggle_edit_panel(info_clicks, close_n, devices):
    triggered = ctx.triggered_id
    hidden = {"display":"none","width":"300px","flexShrink":0}
    visible = {"display":"block","width":"300px","flexShrink":0}
    if triggered == "close-edit-device":
        return hidden, dash.no_update, None
    if not triggered or not any(info_clicks or []):
        return dash.no_update, dash.no_update, dash.no_update
    did    = triggered["index"]
    device = next((d for d in (devices or []) if d.get("id") == did), None)
    if not device:
        return dash.no_update, dash.no_update, dash.no_update
    return visible, device.get("name", ""), did


@callback(
    Output("dm-edit-msg",       "children"),
    Output("device-cards-grid", "children", allow_duplicate=True),
    Output("dm-devices-data",   "data",     allow_duplicate=True),
    Input("dm-save-name-btn",   "n_clicks"),
    State("dm-edit-device-id",  "data"),
    State("dm-edit-name",       "value"),
    State("dm-devices-data",    "data"),
    prevent_initial_call=True,
)
def save_device_name(n, device_id, name, devices):
    if not n or not device_id:
        return dash.no_update, dash.no_update, dash.no_update
    name = (name or "").strip()
    if len(name) < 2:
        return (html.Div("Name must be at least 2 characters.", className="alert-error",
                         style={"marginBottom":"4px"}),
                dash.no_update, dash.no_update)
    result, err = api.rename_device(device_id, name)
    if result is None:
        return (html.Div(err or "Rename failed.", className="alert-error",
                         style={"marginBottom":"4px"}),
                dash.no_update, dash.no_update)
    updated = api.get_devices()
    return (html.Div(f"Renamed to '{name}'.", className="alert-success",
                     style={"marginBottom":"4px"}),
            build_cards(updated), updated)

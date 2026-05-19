import re

import dash
from dash import dcc, html, callback, Input, Output, State, ctx
import plotly.graph_objects as go
import api
import floor_plan
import pages.analytics as anly

dash.register_page(__name__, path="/routers", title="Router Management — Central Link")


def _status_class(count):
    return "badge-active" if count > 0 else "badge-offline"

def _status_label(count):
    return "ACTIVE" if count > 0 else "OFFLINE"


def make_blueprint_click_fig(blueprint_url=None, marker_x=None, marker_y=None):
    fig = go.Figure()
    floor_plan.draw_clinic(fig)
    fig.add_annotation(x=0.5, y=0.99, text="Click anywhere to place router",
                       showarrow=False, font=dict(size=9, color="#8b949e"))

    # Invisible dense grid — Plotly clickData only fires on traces, not shapes
    n = 25
    xs = [i / (n - 1) for i in range(n) for _ in range(n)]
    ys = [j / (n - 1) for _ in range(n) for j in range(n)]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(size=22, color="rgba(0,0,0,0)", opacity=0),
        hoverinfo="none", showlegend=False,
    ))

    # Red placement dot
    if marker_x is not None and marker_y is not None:
        fig.add_trace(go.Scatter(
            x=[marker_x], y=[marker_y], mode="markers",
            marker=dict(size=16, color="#f85149",
                        line=dict(color="#fff", width=2)),
            hoverinfo="skip", showlegend=False,
        ))

    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        height=220, clickmode="event",
    )
    return fig


def router_card(router, devices_count):
    rid    = router["id"]
    status = _status_label(devices_count)
    return html.Div(className="router-card", children=[
        html.Div(status, className=f"router-card-status {_status_class(devices_count)}"),
        html.Div("⊞", style={"fontSize": "22px", "color": "var(--accent-light)"}),
        html.Div(router.get("name", "Unknown"), className="router-card-name"),
        html.Div(router.get("id", "")[:16], className="router-card-loc",
                 style={"fontFamily": "monospace", "fontSize": "10px"}),
        html.Div(className="router-card-meta", children=[
            html.Div([html.Div("SIGNAL", className="router-card-meta-item"),
                      html.Div("Strong", className="router-card-meta-val")]),
            html.Div([html.Div("DEVICES", className="router-card-meta-item"),
                      html.Div(str(devices_count), className="router-card-meta-val")]),
        ]),
        html.Div(style={"display": "flex", "gap": "8px"}, children=[
            html.Button("View Details", n_clicks=0,
                        id={"type": "view-btn", "index": rid},
                        className="btn-outline", style={"flex": 1, "fontSize": "12px"}),
            html.Button("Stats", n_clicks=0,
                        id={"type": "stats-btn", "index": rid},
                        className="btn-outline", style={"fontSize": "12px"}),
        ]),
    ])


def build_cards(routers, routers_map, filter_val="all", search=""):
    cards = []
    for r in routers:
        count  = routers_map.get(r["id"], 0)
        status = _status_label(count).lower()
        if filter_val != "all" and filter_val != status:
            continue
        if search and search.lower() not in r.get("name", "").lower():
            continue
        cards.append(router_card(r, count))
    return cards or [html.Div("No routers match this filter.",
                               style={"color": "var(--text-muted)", "padding": "20px 0"})]


def layout():
    routers       = api.get_routers()
    routers_map   = {r["id"]: r.get("connected_devices_count", 0)
                     for r in api.get_routers_map()}
    blueprint_url = api.get_blueprint()
    total_online  = sum(1 for v in routers_map.values() if v > 0)

    return html.Div([
        dcc.Store(id="rm-routers-data",  data=routers),
        dcc.Store(id="rm-map-data",      data=routers_map),
        dcc.Store(id="rm-selected",      data={"id": None, "mode": None}),
        dcc.Store(id="rm-blueprint-url", data=blueprint_url),
        dcc.Store(id="rm-loc-x",         data=0.5),
        dcc.Store(id="rm-loc-y",         data=0.5),

        html.Div(style={"display":"flex","gap":"12px","alignItems":"center","marginBottom":"24px"}, children=[
            dcc.Input(id="router-search", type="text", debounce=True,
                      placeholder="🔍  Search routers...",
                      className="cl-input", style={"flex": 1}),
            html.Button("+ Add Router", id="open-add-router", className="btn-primary", n_clicks=0),
        ]),

        html.Div(style={"display":"flex","gap":"24px"}, children=[
            html.Div(style={"flex":1}, children=[
                html.Div(style={"display":"flex","justifyContent":"space-between",
                                "alignItems":"flex-start","marginBottom":"20px"}, children=[
                    html.Div([
                        html.Div("Router Management", className="page-title"),
                        html.Div("Monitor and control your connected IoT infrastructure.",
                                 className="page-sub", style={"marginBottom":0}),
                    ]),
                    html.Div(className="cl-card", style={"padding":"10px 18px","textAlign":"center"}, children=[
                        html.Span("TOTAL ONLINE", style={"fontSize":"9px","color":"var(--text-muted)","display":"block"}),
                        html.Span(str(total_online), style={"fontSize":"20px","fontWeight":700}),
                    ]),
                ]),
                html.Div(style={"display":"flex","gap":"8px","marginBottom":"20px"}, children=[
                    html.Button("All Routers", id="rf-all",     n_clicks=0, className="btn-primary",
                                style={"fontSize":"12px","padding":"5px 14px"}),
                    html.Button("Active",      id="rf-active",  n_clicks=0, className="btn-outline",
                                style={"fontSize":"12px","padding":"5px 14px"}),
                    html.Button("Offline",     id="rf-offline", n_clicks=0, className="btn-outline",
                                style={"fontSize":"12px","padding":"5px 14px"}),
                ]),
                html.Div(id="router-cards-grid",
                         style={"display":"grid",
                                "gridTemplateColumns":"repeat(auto-fill, minmax(220px, 1fr))",
                                "gap":"16px"},
                         children=build_cards(routers, routers_map)),
            ]),

            html.Div(id="add-router-panel",
                     style={"display":"none","width":"340px","flexShrink":0}, children=[
                html.Div(className="cl-card", children=[
                    html.Div("Add Router", style={"fontSize":"18px","fontWeight":700,"marginBottom":"4px"}),
                    html.Div("Click the map to set the router location",
                             style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"16px"}),

                    html.Div("ROUTER ID (MAC Address)", className="cl-label"),
                    html.Div(
                        style={"position":"relative","marginBottom":"16px"},
                        children=[
                            dcc.Input(id="new-router-id", type="text",
                                      className="cl-input",
                                      placeholder="XX:XX:XX:XX:XX:XX",
                                      style={"fontFamily":"monospace","fontSize":"11px",
                                             "color":"var(--accent-light)","opacity":1,
                                             "cursor":"text","paddingRight":"70px"}),
                        ],
                    ),

                    html.Div("ROUTER NAME", className="cl-label"),
                    dcc.Input(id="new-router-name", type="text", placeholder="Router Name",
                              className="cl-input", style={"marginBottom":"16px"}),
                    html.Div("CLICK MAP TO SET LOCATION", className="cl-label"),
                    dcc.Graph(id="blueprint-click-map",
                              figure=make_blueprint_click_fig(blueprint_url),
                              config={"displayModeBar":False},
                              style={"marginBottom":"8px","borderRadius":"6px","overflow":"hidden"}),
                    html.Div(id="location-display",
                             style={"fontSize":"11px","color":"var(--text-muted)",
                                    "marginBottom":"16px","textAlign":"center"},
                             children="No location selected — click the map"),
                    html.Div(id="add-router-msg"),
                    html.Button("Add Router", id="add-router-btn", n_clicks=0,
                                className="btn-primary", style={"width":"100%"}),
                ]),
            ]),
        ]),

        html.Div(
            id="router-modal-backdrop",
            style={"display":"none","position":"fixed","top":0,"left":0,
                   "width":"100vw","height":"100vh",
                   "background":"rgba(0,0,0,.75)","zIndex":300,
                   "alignItems":"center","justifyContent":"center"},
            children=[html.Div(className="cl-card",
                style={"width":"580px","maxHeight":"80vh","overflowY":"auto"},
                children=[
                    html.Div(style={"display":"flex","justifyContent":"space-between",
                                    "alignItems":"center","marginBottom":"20px"}, children=[
                        html.Div(id="modal-title", style={"fontSize":"18px","fontWeight":700}),
                        html.Button("✕", id="close-router-modal", n_clicks=0,
                                    className="btn-outline",
                                    style={"padding":"2px 10px","fontSize":"16px"}),
                    ]),
                    html.Div(id="modal-body"),
                ],
            )],
        ),
    ])


@callback(
    Output("rm-loc-x",            "data"),
    Output("rm-loc-y",            "data"),
    Output("blueprint-click-map", "figure"),
    Output("location-display",    "children"),
    Input("blueprint-click-map",  "clickData"),
    State("rm-blueprint-url",     "data"),
    prevent_initial_call=True,
)
def capture_location(click_data, blueprint_url):
    if not click_data:
        return 0.5, 0.5, dash.no_update, "No location selected"
    pt = click_data["points"][0]
    x  = round(float(pt.get("x", 0.5)), 4)
    y  = round(float(pt.get("y", 0.5)), 4)
    return x, y, make_blueprint_click_fig(blueprint_url, x, y), f"X={x:.3f},  Y={y:.3f}"


@callback(
    Output("rm-selected", "data"),
    Input({"type": "view-btn",  "index": dash.ALL}, "n_clicks"),
    Input({"type": "stats-btn", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def capture_click(view_clicks, stats_clicks):
    triggered = ctx.triggered_id
    if not triggered:
        return dash.no_update
    all_clicks = (view_clicks or []) + (stats_clicks or [])
    if not any(all_clicks):
        return dash.no_update
    return {"id": triggered["index"], "mode": triggered["type"]}


@callback(
    Output("router-modal-backdrop", "style"),
    Output("modal-title",           "children"),
    Output("modal-body",            "children"),
    Output("url",                   "pathname", allow_duplicate=True),
    Input("rm-selected",        "data"),
    Input("close-router-modal", "n_clicks"),
    prevent_initial_call=True,
)
def render_modal(selected, close_clicks):
    HIDDEN  = {"display":"none","position":"fixed","top":0,"left":0,
               "width":"100vw","height":"100vh",
               "background":"rgba(0,0,0,.75)","zIndex":300,
               "alignItems":"center","justifyContent":"center"}
    VISIBLE = {**HIDDEN, "display":"flex"}

    triggered = ctx.triggered_id
    if triggered == "close-router-modal":
        return HIDDEN, "", [], dash.no_update
    if not selected or not selected.get("id"):
        return HIDDEN, "", [], dash.no_update

    rid  = selected["id"]
    mode = selected["mode"]

    if mode == "stats-btn":
        return HIDDEN, "", [], f"/router-stats?id={rid}"

    router  = api.get_router(rid) or {"id": rid, "name": rid[:12]}
    name    = router.get("name", rid)
    devices = api.get_router_devices(rid)
    hourly  = api.get_router_hourly_sessions(rid)

    rows = [html.Tr([
        html.Td(d.get("name","—")),
        html.Td(d.get("holder_name","—")),
        html.Td(str(d.get("last_record_timestamp") or "—")[:16],
                style={"color":"var(--text-muted)","fontSize":"11px"}),
    ]) for d in devices]
    hours    = [anly._fmt_hour(h.get("hour", "")) for h in hourly]
    sess_cnt = [h.get("sessions_count", 0) for h in hourly]
    sess_fig = go.Figure()
    sess_fig.add_trace(go.Bar(x=hours, y=sess_cnt,
        marker_color=["#1f6feb" if i < len(sess_cnt)-1 else "#58a6ff"
                      for i in range(len(sess_cnt))]))
    sess_fig.update_layout(
        paper_bgcolor="#1c2230", plot_bgcolor="#1c2230",
        font=dict(color="#8b949e", size=10),
        margin=dict(l=36, r=12, t=12, b=36),
        showlegend=False, bargap=0.25, height=180,
        xaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
        yaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
    )

    body = html.Div([
        html.Div(style={"display":"flex","gap":"14px","marginBottom":"16px"}, children=[
            html.Div(className="stat-card", style={"flex":1,"padding":"12px"}, children=[
                html.Div("DEVICES", className="stat-label"),
                html.Div(str(len(devices)), className="stat-value", style={"fontSize":"22px"}),
            ]),
            html.Div(className="stat-card", style={"flex":1,"padding":"12px"}, children=[
                html.Div("STATUS", className="stat-label"),
                html.Div("ACTIVE" if devices else "OFFLINE",
                         className="badge-active" if devices else "badge-offline",
                         style={"marginTop":"8px","display":"inline-block"}),
            ]),
            html.Div(className="stat-card", style={"flex":1,"padding":"12px"}, children=[
                html.Div("SIGNAL", className="stat-label"),
                html.Div("Strong", style={"fontSize":"14px","fontWeight":600,
                                          "color":"var(--green)","marginTop":"8px"}),
            ]),
        ]),
        html.Div("Hourly Sessions", className="section-title", style={"marginBottom":"6px"}),
        dcc.Graph(figure=sess_fig, config={"displayModeBar":False}, style={"marginBottom":"16px"}),
        html.Div(f"Connected Devices ({len(devices)})", className="section-title",
                 style={"marginBottom":"10px"}),
        html.Table(className="cl-table", children=[
            html.Thead(html.Tr([html.Th("Device"), html.Th("Holder"), html.Th("Last Seen")])),
            html.Tbody(rows if rows else [
                html.Tr(html.Td("No devices connected.", colSpan=3,
                                style={"color":"var(--text-muted)","padding":"16px 14px"}))
            ]),
        ]),
    ])
    return VISIBLE, name, body, dash.no_update


@callback(
    Output("router-cards-grid", "children"),
    Output("rf-all",    "className"),
    Output("rf-active", "className"),
    Output("rf-offline","className"),
    Input("rf-all",        "n_clicks"),
    Input("rf-active",     "n_clicks"),
    Input("rf-offline",    "n_clicks"),
    Input("router-search", "value"),
    State("rm-routers-data", "data"),
    State("rm-map-data",     "data"),
    prevent_initial_call=True,
)
def filter_cards(n_all, n_active, n_offline, search, routers, routers_map):
    tid    = ctx.triggered_id or "rf-all"
    fmap   = {"rf-all":"all","rf-active":"active","rf-offline":"offline"}
    active = fmap.get(tid,"all") if tid in fmap else "all"
    cards  = build_cards(routers or [], routers_map or {}, active, search or "")
    cls    = lambda k: "btn-primary" if active == k else "btn-outline"
    return cards, cls("all"), cls("active"), cls("offline")


@callback(
    Output("add-router-panel", "style"),
    Input("open-add-router", "n_clicks"),
    State("add-router-panel", "style"),
    prevent_initial_call=True,
)
def toggle_add_panel(n, style):
    return {**style, "display": "block" if style.get("display") == "none" else "none"}


@callback(
    Output("add-router-msg",        "children"),
    Output("rm-routers-data",       "data"),
    Output("router-cards-grid",     "children", allow_duplicate=True),
    Output("new-router-id",        "value"),
    Output("new-router-name",       "value"),
    Output("rm-loc-x",             "data", allow_duplicate=True),
    Output("rm-loc-y",             "data", allow_duplicate=True),
    Input("add-router-btn",  "n_clicks"),
    State("new-router-id",   "value"),
    State("new-router-name", "value"),
    State("rm-loc-x",        "data"),
    State("rm-loc-y",        "data"),
    State("rm-routers-data", "data"),
    State("rm-map-data",     "data"),
    prevent_initial_call=True,
)
def add_router(n, rid, name, loc_x, loc_y, routers, routers_map):
    no_change = (dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    if not rid or not re.fullmatch(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", rid):
        return (html.Div("Router ID is invalid.", className="alert-error",
                         style={"marginBottom":"8px"}),
                dash.no_update, dash.no_update, *no_change)
    if not name:
        return (html.Div("Router name is required.", className="alert-error",
                         style={"marginBottom":"8px"}),
                dash.no_update, dash.no_update, *no_change)
    lx = max(0.01, float(loc_x or 0.5))
    ly = max(0.01, float(loc_y or 0.5))
    result, err = api.create_router(rid, name, lx, ly)
    if result is None:
        return (html.Div(err or "Failed to save",
                         className="alert-error", style={"marginBottom":"8px"}),
                dash.no_update, dash.no_update, *no_change)
    new_entry = {"id": rid, "name": name, "location_x": lx, "location_y": ly}
    updated   = (routers or []) + [new_entry]
    return (html.Div(f"'{name}' added successfully.", className="alert-success",
                     style={"marginBottom":"8px"}),
            updated,
            build_cards(updated, routers_map or {}),
            '', '', lx, ly)

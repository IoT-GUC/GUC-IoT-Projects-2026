from datetime import datetime, timezone

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import api

dash.register_page(__name__, path="/router-stats", title="Router Stats — Central Link")

CHART_LAYOUT = dict(
    paper_bgcolor="#1c2230", plot_bgcolor="#1c2230",
    font=dict(color="#8b949e", size=10),
    margin=dict(l=40, r=16, t=16, b=40),
    showlegend=False, height=220,
    xaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
    yaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
)


def _relative_time(ts_str):
    ts = (str(ts_str or "")).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        diff = int((datetime.now(timezone.utc) - dt).total_seconds())
        if diff < 60:    return f"{diff}s ago"
        if diff < 3600:  return f"{diff//60}m ago"
        if diff < 86400: return f"{diff//3600}h ago"
        return f"{diff//86400}d ago"
    except Exception:
        return str(ts_str)[:16] if ts_str else "—"


def layout(**kwargs):
    # Read router_id from URL search params (passed via dcc.Location)
    return html.Div([
        dcc.Location(id="rs-url", refresh=False),
        html.Div(id="rs-content"),
    ])


@callback(
    Output("rs-content", "children"),
    Input("rs-url",      "search"),
)
def render_router_stats(search):
    rid = ""
    if search:
        for part in search.lstrip("?").split("&"):
            if part.startswith("id="):
                rid = part[3:]
                break

    if not rid:
        return html.Div([
            html.Div("Router Stats", className="page-title"),
            html.Div("No router ID provided.", style={"color":"var(--text-muted)","marginTop":"16px"}),
            dcc.Link("← Back to Router Management", href="/routers",
                     style={"color":"var(--accent-light)","fontSize":"13px"}),
        ])

    router  = api.get_router(rid) or {"id": rid, "name": rid[:12]}
    devices = api.get_router_devices(rid)
    hourly  = api.get_router_hourly_sessions(rid)
    name    = router.get("name", rid)

    hours    = [str(h.get("hour",""))[-8:-3] for h in hourly]
    sess_cnt = [h.get("sessions_count", 0) for h in hourly]
    avg_dur  = [round((h.get("average_session_duration") or 0) / 60, 1) for h in hourly]

    sessions_fig = go.Figure()
    sessions_fig.add_trace(go.Bar(
        x=hours, y=sess_cnt,
        marker_color=["#1f6feb" if i < len(sess_cnt)-1 else "#58a6ff"
                      for i in range(len(sess_cnt))],
        name="Sessions",
    ))
    sessions_fig.update_layout(**CHART_LAYOUT, bargap=0.25)

    duration_fig = go.Figure()
    duration_fig.add_trace(go.Scatter(
        x=hours, y=avg_dur, mode="lines+markers",
        line=dict(color="#3fb950", width=2),
        marker=dict(size=5, color="#3fb950"),
        fill="tozeroy", fillcolor="rgba(63,185,80,0.07)",
        name="Avg Duration (min)",
    ))
    duration_fig.update_layout(**{**CHART_LAYOUT,
        "yaxis": dict(gridcolor="#21262d", zeroline=False,
                      ticksuffix="m", tickfont=dict(size=9))})

    device_rows = [html.Tr([
        html.Td(html.Div(style={"display":"flex","alignItems":"center","gap":"10px"}, children=[
            html.Div((d.get("name") or "?")[0].upper(), style={
                "width":"30px","height":"30px","borderRadius":"50%",
                "background":"linear-gradient(135deg,#6e40c9,#1f6feb)",
                "display":"flex","alignItems":"center","justifyContent":"center",
                "fontSize":"11px","fontWeight":700,"color":"#fff","flexShrink":0,
            }),
            html.Div(d.get("name","—"), style={"fontWeight":600,"fontSize":"13px"}),
        ])),
        html.Td(d.get("holder_name","—"), style={"fontSize":"12px"}),
        html.Td(_relative_time(d.get("last_record_timestamp")),
                style={"fontSize":"11px","color":"var(--text-muted)"}),
    ]) for d in devices]

    return html.Div([
        html.Div(style={"display":"flex","alignItems":"center","gap":"16px","marginBottom":"8px"}, children=[
            dcc.Link("←", href="/routers",
                     style={"color":"var(--accent-light)","fontSize":"20px","textDecoration":"none"}),
            html.Div(name, className="page-title", style={"marginBottom":0}),
        ]),
        html.Div(f"Router ID: {rid}", style={"fontSize":"11px","color":"var(--text-muted)","marginBottom":"24px"}),

        html.Div(style={"display":"grid","gridTemplateColumns":"repeat(3,1fr)","gap":"14px","marginBottom":"24px"}, children=[
            html.Div(className="stat-card", children=[
                html.Div("CONNECTED DEVICES", className="stat-label"),
                html.Div(str(len(devices)), className="stat-value"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("TOTAL SESSIONS (SHOWN)", className="stat-label"),
                html.Div(str(sum(sess_cnt)), className="stat-value"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("STATUS", className="stat-label"),
                html.Div("ACTIVE" if devices else "OFFLINE",
                         className="badge-active" if devices else "badge-offline",
                         style={"marginTop":"10px","display":"inline-block"}),
            ]),
        ]),

        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px","marginBottom":"24px"}, children=[
            html.Div(className="cl-card", children=[
                html.Div("Hourly Sessions", className="section-title", style={"marginBottom":"8px"}),
                dcc.Graph(figure=sessions_fig, config={"displayModeBar":False}),
            ]),
            html.Div(className="cl-card", children=[
                html.Div("Avg Session Duration (min)", className="section-title", style={"marginBottom":"8px"}),
                dcc.Graph(figure=duration_fig, config={"displayModeBar":False}),
            ]),
        ]),

        html.Div(className="cl-card", children=[
            html.Div(f"Connected Devices ({len(devices)})", className="section-title",
                     style={"marginBottom":"14px"}),
            html.Table(className="cl-table", children=[
                html.Thead(html.Tr([html.Th("DEVICE"), html.Th("HOLDER"), html.Th("LAST SEEN")])),
                html.Tbody(device_rows if device_rows else [
                    html.Tr(html.Td("No devices connected.", colSpan=3,
                                    style={"color":"var(--text-muted)","padding":"16px 14px"}))
                ]),
            ]),
        ]),
    ])

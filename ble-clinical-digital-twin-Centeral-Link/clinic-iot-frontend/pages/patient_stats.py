from datetime import datetime, timezone

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import api

dash.register_page(__name__, path="/patient-stats", title="Patient Stats — Central Link")

CHART_LAYOUT = dict(
    paper_bgcolor="#1c2230", plot_bgcolor="#1c2230",
    font=dict(color="#8b949e", size=10),
    margin=dict(l=40, r=16, t=16, b=40),
    showlegend=False, height=220,
    xaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
    yaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
)


def _fmt_duration(seconds):
    if not seconds:
        return "—"
    seconds = int(seconds)
    h, rem  = divmod(seconds, 3600)
    m, s    = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m {s}s"


def _fmt_ts(ts_str):
    ts = (str(ts_str or "")).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%b %d, %H:%M")
    except Exception:
        return str(ts_str)[:16] if ts_str else "—"


def layout(**kwargs):
    return html.Div([
        dcc.Location(id="ps-url", refresh=False),
        html.Div(id="ps-content"),
    ])


@callback(
    Output("ps-content", "children"),
    Input("ps-url",      "search"),
)
def render_patient_stats(search):
    pid = ""
    if search:
        for part in search.lstrip("?").split("&"):
            if part.startswith("id="):
                pid = part[3:]
                break

    if not pid:
        return html.Div([
            html.Div("Patient Stats", className="page-title"),
            html.Div("No patient ID provided.", style={"color":"var(--text-muted)","marginTop":"16px"}),
            dcc.Link("← Back to Patient Tracking", href="/patients",
                     style={"color":"var(--accent-light)","fontSize":"13px"}),
        ])

    # Find patient name from patients list
    patients    = api.get_patients()
    patient     = next((p for p in patients if p.get("id") == pid), {"id":pid,"name":pid[:12]})
    sessions    = api.get_patient_sessions(pid)
    name        = patient.get("name", pid[:12])

    total_time  = sum(s.get("duration") or 0 for s in sessions)
    router_visits = {}
    for s in sessions:
        rn = s.get("router_name","Unknown")
        router_visits[rn] = router_visits.get(rn, 0) + 1

    # Timeline chart — session start + duration
    if sessions:
        starts    = [_fmt_ts(s.get("start_time")) for s in sessions]
        durations = [round((s.get("duration") or 0)/60, 1) for s in sessions]
        routers   = [s.get("router_name","?") for s in sessions]
        timeline_fig = go.Figure()
        timeline_fig.add_trace(go.Bar(
            x=starts, y=durations,
            marker_color="#9d5cf5",
            text=routers,
            textposition="inside",
            textfont=dict(size=8, color="#fff"),
            name="Duration (min)",
        ))
        timeline_fig.update_layout(**{**CHART_LAYOUT,
            "yaxis": dict(gridcolor="#21262d", zeroline=False,
                          ticksuffix="m", tickfont=dict(size=9)),
            "bargap": 0.2})
    else:
        timeline_fig = go.Figure()
        timeline_fig.update_layout(**CHART_LAYOUT)
        timeline_fig.add_annotation(x=0.5, y=0.5, xref="paper", yref="paper",
            text="No session data", showarrow=False,
            font=dict(size=12, color="#4a5568"))

    # Router visit breakdown pie
    if router_visits:
        pie_fig = go.Figure(go.Pie(
            labels=list(router_visits.keys()),
            values=list(router_visits.values()),
            hole=0.4,
            marker=dict(colors=["#1f6feb","#9d5cf5","#3fb950","#f85149","#d29922"]),
            textfont=dict(size=10),
        ))
        pie_fig.update_layout(
            paper_bgcolor="#1c2230",
            margin=dict(l=16, r=16, t=16, b=16),
            showlegend=True,
            legend=dict(font=dict(color="#8b949e", size=10)),
            height=220,
        )
    else:
        pie_fig = go.Figure()
        pie_fig.update_layout(paper_bgcolor="#1c2230", height=220)

    session_rows = [html.Tr([
        html.Td(s.get("router_name","—"), style={"fontSize":"13px"}),
        html.Td(_fmt_ts(s.get("start_time")),
                style={"fontSize":"12px","color":"var(--text-muted)"}),
        html.Td(_fmt_duration(s.get("duration")), style={"fontSize":"12px"}),
    ]) for s in sessions]

    return html.Div([
        html.Div(style={"display":"flex","alignItems":"center","gap":"16px","marginBottom":"8px"}, children=[
            dcc.Link("←", href="/patients",
                     style={"color":"var(--accent-light)","fontSize":"20px","textDecoration":"none"}),
            html.Div(name, className="page-title", style={"marginBottom":0}),
        ]),
        html.Div(f"Patient ID: {pid}", style={"fontSize":"11px","color":"var(--text-muted)","marginBottom":"24px"}),

        html.Div(style={"display":"grid","gridTemplateColumns":"repeat(3,1fr)","gap":"14px","marginBottom":"24px"}, children=[
            html.Div(className="stat-card", children=[
                html.Div("TOTAL SESSIONS", className="stat-label"),
                html.Div(str(len(sessions)), className="stat-value"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("TOTAL TIME", className="stat-label"),
                html.Div(_fmt_duration(total_time), className="stat-value"),
            ]),
            html.Div(className="stat-card", children=[
                html.Div("ROUTERS VISITED", className="stat-label"),
                html.Div(str(len(router_visits)), className="stat-value"),
            ]),
        ]),

        html.Div(style={"display":"grid","gridTemplateColumns":"2fr 1fr","gap":"16px","marginBottom":"24px"}, children=[
            html.Div(className="cl-card", children=[
                html.Div("Session Timeline (duration per visit)", className="section-title",
                         style={"marginBottom":"8px"}),
                dcc.Graph(figure=timeline_fig, config={"displayModeBar":False}),
            ]),
            html.Div(className="cl-card", children=[
                html.Div("Router Visits Breakdown", className="section-title",
                         style={"marginBottom":"8px"}),
                dcc.Graph(figure=pie_fig, config={"displayModeBar":False}),
            ]),
        ]),

        html.Div(className="cl-card", children=[
            html.Div(f"All Sessions ({len(sessions)})", className="section-title",
                     style={"marginBottom":"14px"}),
            html.Table(className="cl-table", children=[
                html.Thead(html.Tr([html.Th("ROUTER"), html.Th("START TIME"), html.Th("DURATION")])),
                html.Tbody(session_rows if session_rows else [
                    html.Tr(html.Td("No sessions recorded.", colSpan=3,
                                    style={"color":"var(--text-muted)","padding":"16px 14px"}))
                ]),
            ]),
        ]),
    ])

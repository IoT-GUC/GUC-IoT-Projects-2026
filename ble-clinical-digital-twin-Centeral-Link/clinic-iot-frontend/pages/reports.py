from datetime import datetime

import dash
from dash import html, dcc
import plotly.graph_objects as go
import api

dash.register_page(__name__, path="/reports", title="Reports — Central Link")

CHART_LAYOUT = dict(
    paper_bgcolor="#1c2230",
    plot_bgcolor="#1c2230",
    font=dict(color="#8b949e", size=10),
    margin=dict(l=40, r=16, t=16, b=40),
    showlegend=False,
    xaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
    yaxis=dict(gridcolor="#21262d", zeroline=False, tickfont=dict(size=9)),
    height=220,
)


def _fmt_seconds(sec) -> str:
    s = int(sec or 0)
    if s <= 0:   return "—"
    if s < 60:   return f"{s}s"
    if s < 3600: return f"{s // 60}m {s % 60}s"
    return f"{s // 3600}h {(s % 3600) // 60}m"


def _fmt_hour(val) -> str:
    if hasattr(val, "strftime"):
        return val.strftime("%H:%M")
    s = str(val or "").strip()
    for sep in ("T", " "):
        if sep in s:
            return s.split(sep)[1][:5]
    return s[-8:-3] if len(s) >= 8 else s


def peak_hours_fig(hourly_devices: list) -> go.Figure:
    if not hourly_devices:
        fig = go.Figure()
        fig.update_layout(**CHART_LAYOUT)
        return fig

    hours  = [_fmt_hour(h.get("hour", "")) for h in hourly_devices]
    counts = [h.get("patients_count", 0) or h.get("devices_count", 0)
              for h in hourly_devices]

    # Top-3 hours get a brighter color
    sorted_idx = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)
    top3       = set(sorted_idx[:3])
    colors     = ["#f0883e" if i in top3 else "#1f6feb" for i in range(len(counts))]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=hours, y=counts,
        marker_color=colors,
        hovertemplate="%{x}: %{y} patients<extra></extra>",
    ))
    fig.update_layout(**{**CHART_LAYOUT, "bargap": 0.25})
    return fig


def efficiency_fig(rooms_dwell: list) -> go.Figure:
    """Patients processed per hour per room = 3600 / avg_dwell_seconds."""
    fig = go.Figure()
    if not rooms_dwell:
        fig.update_layout(**CHART_LAYOUT)
        return fig

    names      = [r.get("router_name", "?") for r in rooms_dwell]
    avg_dwell  = [max(r.get("avg_dwell_seconds", 1), 1) for r in rooms_dwell]
    throughput = [round(3600 / d, 1) for d in avg_dwell]   # patients/hour

    fig.add_trace(go.Bar(
        x=names, y=throughput,
        marker=dict(
            color=throughput,
            colorscale=[[0, "#f85149"], [0.5, "#e3b341"], [1, "#3fb950"]],
            showscale=False,
        ),
        text=[f"{t}/hr" for t in throughput],
        textposition="outside",
        hovertemplate="%{x}<br>%{y:.1f} patients/hr<extra></extra>",
    ))
    fig.update_layout(**{
        **CHART_LAYOUT,
        "yaxis": dict(gridcolor="#21262d", zeroline=False,
                      ticksuffix="/hr", tickfont=dict(size=9)),
    })
    return fig


def layout():
    hourly_devices = api.get_hourly_devices()
    rooms_dwell    = api.get_rooms_dwell_time()
    avg_visit      = api.get_avg_visit_time()
    routers_map    = api.get_routers_map()

    # Daily summary numbers
    patients_today = avg_visit.get("patient_count", 0)
    avg_visit_secs = int(avg_visit.get("avg_visit_seconds") or 0)
    avg_visit_str  = _fmt_seconds(avg_visit_secs)

    busiest = max(routers_map, key=lambda r: r.get("connected_devices_count", 0), default=None)
    busiest_name = busiest.get("id", "—")[:12] if busiest else "—"
    busiest_pts  = busiest.get("connected_devices_count", 0) if busiest else 0

    total_sessions_today = sum(r.get("total_sessions", 0) for r in rooms_dwell)

    # Figures
    peak_fig  = peak_hours_fig(hourly_devices)
    effic_fig = efficiency_fig(rooms_dwell)

    # Queue durations table rows
    queue_rows = [
        html.Tr([
            html.Td(html.Div(style={"display": "flex", "alignItems": "center",
                                    "gap": "8px"}, children=[
                html.Div(str(i + 1), style={
                    "width": "22px", "height": "22px", "borderRadius": "50%",
                    "background": "#1f6feb" if i == 0 else "#21262d",
                    "display": "flex", "alignItems": "center",
                    "justifyContent": "center", "fontSize": "10px",
                    "fontWeight": 700, "color": "#fff", "flexShrink": 0,
                }),
                html.Div(r.get("router_name", "—"), style={"fontWeight": 600}),
            ])),
            html.Td(str(r.get("total_sessions", 0))),
            html.Td(_fmt_seconds(r.get("avg_dwell_seconds", 0))),
            html.Td(_fmt_seconds(r.get("total_dwell_seconds", 0)),
                    style={"color": "var(--text-muted)"}),
        ])
        for i, r in enumerate(rooms_dwell)
    ] or [html.Tr(html.Td("No data.", colSpan=4,
                           style={"color": "var(--text-muted)", "padding": "20px 14px"}))]

    today_str = datetime.now().strftime("%A, %B %d %Y")

    return html.Div([
        html.Div(style={"display": "flex", "justifyContent": "space-between",
                        "alignItems": "center", "marginBottom": "24px"}, children=[
            html.Div([
                html.Div("Clinic Reports", className="page-title",
                         style={"marginBottom": "2px"}),
                html.Div(today_str,
                         style={"fontSize": "12px", "color": "var(--text-muted)"}),
            ]),
        ]),

        # Daily summary cards
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
                   "gap": "14px", "marginBottom": "24px"},
            children=[
                html.Div(className="stat-card", children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                        html.Div("Patients Today", className="stat-label"),
                        html.Span("👥", style={"fontSize": "16px"}),
                    ]),
                    html.Div(str(patients_today), className="stat-value"),
                    html.Div("from /records/avg-visit-time",
                             style={"fontSize": "10px", "color": "var(--text-muted)"}),
                ]),
                html.Div(className="stat-card", children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                        html.Div("Total Sessions", className="stat-label"),
                        html.Span("📋", style={"fontSize": "16px"}),
                    ]),
                    html.Div(str(total_sessions_today), className="stat-value"),
                    html.Div("across all rooms today",
                             style={"fontSize": "10px", "color": "var(--text-muted)"}),
                ]),
                html.Div(className="stat-card", children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                        html.Div("Avg Visit Duration", className="stat-label"),
                        html.Span("⏱", style={"fontSize": "16px"}),
                    ]),
                    html.Div(avg_visit_str, className="stat-value"),
                    html.Div("per patient today",
                             style={"fontSize": "10px", "color": "var(--text-muted)"}),
                ]),
                html.Div(className="stat-card", children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                        html.Div("Busiest Room Now", className="stat-label"),
                        html.Span("📍", style={"fontSize": "16px"}),
                    ]),
                    html.Div(busiest_name, className="stat-value",
                             style={"fontSize": "18px"}),
                    html.Div(f"{busiest_pts} patient(s) currently",
                             style={"fontSize": "10px", "color": "var(--text-muted)"}),
                ]),
            ],
        ),

        # Peak hours + Department efficiency
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                   "gap": "16px", "marginBottom": "20px"},
            children=[
                html.Div(className="cl-card", children=[
                    html.Div(className="section-header", children=[
                        html.Div("Peak Hours", className="section-title"),
                        html.Div([
                            html.Span("■ ", style={"color": "#f0883e"}),
                            "Top-3 busiest hours highlighted",
                        ], style={"fontSize": "11px", "color": "var(--text-muted)"}),
                    ]),
                    dcc.Graph(figure=peak_fig, config={"displayModeBar": False}),
                ]),
                html.Div(className="cl-card", children=[
                    html.Div(className="section-header", children=[
                        html.Div("Department Efficiency", className="section-title"),
                        html.Div("Estimated patients processed per hour per room",
                                 style={"fontSize": "11px", "color": "var(--text-muted)"}),
                    ]),
                    dcc.Graph(figure=effic_fig, config={"displayModeBar": False}),
                ]),
            ],
        ),

        # Queue durations table
        html.Div(className="cl-card", children=[
            html.Div(className="section-header", children=[
                html.Div("Queue Durations — Room Ranking", className="section-title"),
                html.Div("Rooms ranked by average patient dwell time (all time)",
                         style={"fontSize": "11px", "color": "var(--text-muted)"}),
            ]),
            html.Table(
                className="cl-table",
                children=[
                    html.Thead(html.Tr([
                        html.Th("ROOM"),
                        html.Th("TOTAL SESSIONS"),
                        html.Th("AVG DWELL TIME"),
                        html.Th("TOTAL TIME IN ROOM"),
                    ])),
                    html.Tbody(queue_rows),
                ],
            ),
        ]),
    ])

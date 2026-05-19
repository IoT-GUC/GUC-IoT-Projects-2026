import dash
from dash import dcc, html, Input, Output, State
import flask
import api
import dotenv
import os


dotenv.load_dotenv()

SERVER_SECRET = (os.getenv("SERVER_SECRET") or "").strip()
SERVER_HOST   = (os.getenv("SERVER_HOST", "127.0.0.1") or "").strip()
SERVER_PORT   = int(os.getenv("SERVER_PORT", 8050))
DEBUG_MODE    = os.getenv("DEBUG_MODE", "false").strip().lower() == "true"


server = flask.Flask(__name__)
server.secret_key = SERVER_SECRET

app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[],
    title="Central Link — IoT Management",
)

NAV_ITEMS = [
    ("⊞", "Dashboard",          "/"),
    ("▣", "Router Management",  "/routers"),
    ("◉", "Device Management",  "/devices"),
    ("◎", "Patient Tracking",   "/patients"),
    ("⟁", "Analytics",          "/analytics"),
    ("📋", "Reports",            "/reports"),
    ("⚙", "Settings",           "/settings"),
]


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    dcc.Interval(id="token-check-interval", interval=60_000, n_intervals=0),

    html.Div(
        id="sidebar",
        children=[
            html.Div(
                className="sidebar-logo",
                children=[
                    html.Div("🔗", className="sidebar-logo-icon"),
                    html.Div([
                        html.Div("Central Link", className="sidebar-logo-text"),
                        html.Div("IoT Management", className="sidebar-logo-sub"),
                    ]),
                ],
            ),
            html.Nav(
                id="sidebar-nav",
                className="sidebar-nav",
                children=[
                    dcc.Link(
                        [html.Span(icon, style={"fontSize": "15px"}), label],
                        href=href,
                        id=f"nav-{href.strip('/') or 'home'}",
                        className="nav-link",
                    )
                    for icon, label, href in NAV_ITEMS
                ],
            ),
            html.Div(id="sidebar-user", className="sidebar-user", children=[
                html.Div("A", className="avatar", id="sidebar-avatar"),
                html.Div([
                    html.Div("Admin", className="avatar-name", id="sidebar-name"),
                    html.Div("System Admin", className="avatar-role"),
                ]),
            ]),
        ],
    ),

    html.Div(id="page-content", children=dash.page_container),
    html.Div(id="login-overlay"),
])


@app.callback(
    Output("login-overlay", "children"),
    Output("sidebar",       "style"),
    Output("page-content",  "style"),
    Input("url",            "pathname"),
    State("session-store",  "data"),
)
def route(pathname, session):
    logged_in = session and session.get("token")

    # Restore token into api module AND Flask server-side session on every navigation
    if logged_in:
        token = session["token"]
        api.set_token(token)
        flask.session["token"] = token

    if not logged_in:
        from pages.login import layout as login_layout
        return (
            login_layout(),
            {"display": "none"},
            {"display": "none"},
        )

    return (
        [],
        {},
        {"marginLeft": "168px", "minHeight": "100vh",
         "background": "var(--bg-primary)", "padding": "28px 32px"},
    )


@app.callback(
    Output("sidebar-name",   "children"),
    Output("sidebar-avatar", "children"),
    Input("session-store", "data"),
)
def update_sidebar_user(session):
    if not session:
        return "Admin", "A"
    name = session.get("admin_name") or session.get("name") or "Admin"
    initials = "".join(w[0].upper() for w in name.split()[:2])
    return name, initials


@app.callback(
    *[Output(f"nav-{href.strip('/') or 'home'}", "className") for _, _, href in NAV_ITEMS],
    Input("url", "pathname"),
)
def update_nav(pathname):
    return [
        "nav-link active" if pathname == href else "nav-link"
        for _, _, href in NAV_ITEMS
    ]


@app.callback(
    Output("session-store", "data",     allow_duplicate=True),
    Output("url",           "pathname", allow_duplicate=True),
    Input("token-check-interval", "n_intervals"),
    State("session-store", "data"),
    prevent_initial_call=True,
)
def check_token_expiry(n, session):
    if not session or not session.get("token"):
        return dash.no_update, dash.no_update
    if not api.token_is_valid():
        api.set_token(None)
        return None, "/"
    return dash.no_update, dash.no_update


if __name__ == "__main__":
    app.run(debug=DEBUG_MODE, host=SERVER_HOST, port=SERVER_PORT)

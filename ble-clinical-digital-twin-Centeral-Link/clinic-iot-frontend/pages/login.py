import dash
from dash import dcc, html, Input, Output, State, callback
import flask
import api

dash.register_page(__name__, path="/login", title="Login — Central Link")

FEATURES = [
    "HIPAA Compliant Infrastructure",
    "Millisecond Data Latency",
    "AI-Driven Predictive Alerts",
]


def layout():
    return html.Div(
        id="login-page",
        children=[
            html.Div(
                className="login-left",
                children=[
                    html.Div(
                        className="login-brand",
                        children=[
                            html.Div("🔗", className="login-brand-icon"),
                            html.Span("Central Link", style={"fontWeight": 700, "fontSize": "18px"}),
                        ],
                    ),
                    html.H1(
                        className="login-headline",
                        children=["Next-Gen ", html.Span("IoT & AI"), " Monitoring Dashboard"],
                    ),
                    html.P(
                        "Seamlessly integrate medical devices, monitor patient vitals "
                        "in real-time, and leverage predictive AI analytics for your "
                        "healthcare facility.",
                        className="login-tagline",
                    ),
                    *[html.Div([html.Div(className="login-feature-dot"), f],
                               className="login-feature") for f in FEATURES],
                ],
            ),
            html.Div(
                className="login-right",
                children=[
                    html.Div(
                        className="login-form-box",
                        children=[
                            html.Div("Welcome Back", className="login-form-title"),
                            html.Div("Access your secure clinical workspace", className="login-form-sub"),
                            html.Div("HOSPITAL ID", className="cl-label"),
                            dcc.Input(id="login-hospital-id", type="text",
                                      placeholder="HOSPITAL-SEED",
                                      className="cl-input", style={"marginBottom": "14px"}),
                            html.Div("PASSWORD", className="cl-label"),
                            dcc.Input(id="login-password", type="password",
                                      placeholder="••••••••",
                                      className="cl-input", style={"marginBottom": "4px"}),
                            html.Div(id="login-error", className="login-error"),
                            html.Button("Initialize Secure Session →",
                                        id="login-btn", className="login-btn", n_clicks=0),
                        ],
                    ),
                    html.Div(
                        className="login-form-box",
                        children=[
                            html.Div("Facility Onboarding", className="login-form-title"),
                            html.Div("Register your hospital for the AI monitoring suite",
                                     className="login-form-sub"),
                            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                                            "gap": "12px", "marginBottom": "14px"}, children=[
                                html.Div([
                                    html.Div("HOSPITAL NAME", className="cl-label"),
                                    dcc.Input(id="reg-name", type="text",
                                              placeholder="St. Margaret's Medical Center",
                                              className="cl-input"),
                                ]),
                                html.Div([
                                    html.Div("HOSPITAL ID", className="cl-label"),
                                    dcc.Input(id="reg-hospital-id", type="text",
                                              placeholder="HOSP-0001",
                                              className="cl-input"),
                                ]),
                            ]),
                            html.Div("ADDRESS", className="cl-label"),
                            dcc.Input(id="reg-address", type="text",
                                      placeholder="123 Healthcare Ave, New Cairo",
                                      className="cl-input", style={"marginBottom": "14px"}),
                            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                                            "gap": "12px", "marginBottom": "14px"}, children=[
                                html.Div([
                                    html.Div("ADMIN NAME", className="cl-label"),
                                    dcc.Input(id="reg-admin-name", type="text",
                                              placeholder="Dr. Sarah Chen", className="cl-input"),
                                ]),
                                html.Div([
                                    html.Div("ADMIN EMAIL", className="cl-label"),
                                    dcc.Input(id="reg-email", type="email",
                                              placeholder="s.chen@hospital.com", className="cl-input"),
                                ]),
                            ]),
                            html.Div("ADMIN PASSWORD", className="cl-label"),
                            dcc.Input(id="reg-password", type="password",
                                      placeholder="Create a strong password",
                                      className="cl-input", style={"marginBottom": "4px"}),
                            html.Div(id="reg-msg"),
                            html.Button("Request Facility Access", id="reg-btn",
                                        className="login-btn", n_clicks=0,
                                        style={"background": "#21262d", "border": "1px solid #30363d"}),
                        ],
                    ),
                    html.Div("© 2024 Central Link Solutions. All rights reserved.",
                             style={"textAlign": "center", "fontSize": "11px",
                                    "color": "var(--text-muted)", "marginTop": "8px"}),
                ],
            ),
        ],
    )


def _extract_session(data: dict) -> dict:
    """Pull consistent keys from whatever the API returns."""
    token = (data.get("token") or data.get("access_token") or
             data.get("data", {}).get("token", ""))
    hospital = data.get("hospital") or data.get("data") or data
    return {
        "token":       token,
        "hospital_id": hospital.get("hospital_id") or hospital.get("id") or data.get("hospital_id", ""),
        "name":        hospital.get("name") or data.get("name", ""),
        "admin_name":  hospital.get("admin_name") or data.get("admin_name", ""),
        "admin_email": hospital.get("admin_email") or data.get("admin_email", ""),
        "address":     hospital.get("address") or data.get("address", ""),
    }


@callback(
    Output("session-store",  "data"),
    Output("login-error",    "children"),
    Output("url",            "pathname", allow_duplicate=True),
    Input("login-btn",       "n_clicks"),
    State("login-hospital-id", "value"),
    State("login-password",    "value"),
    prevent_initial_call=True,
)
def do_login(n, hospital_id, password):
    if not n or not hospital_id or not password:
        return dash.no_update, "", dash.no_update
    result, err = api.login(hospital_id.strip(), password)
    if result and result.get("token"):
        token = result["token"]
        api.set_token(token)
        flask.session["token"] = token
        session = {
            "token":       token,
            "hospital_id": hospital_id.strip(),
            "admin_name":  hospital_id.strip(),
            "name":        hospital_id.strip(),
            "address":     "",
            "admin_email": "",
        }
        return session, "", "/"
    return dash.no_update, err or "Invalid Hospital ID or password.", dash.no_update


@callback(
    Output("reg-msg", "children"),
    Input("reg-btn",  "n_clicks"),
    State("reg-name",       "value"),
    State("reg-hospital-id","value"),
    State("reg-address",    "value"),
    State("reg-admin-name", "value"),
    State("reg-email",      "value"),
    State("reg-password",   "value"),
    prevent_initial_call=True,
)
def do_register(n, name, hospital_id, address, admin_name, email, password):
    if not n:
        return ""
    if not all([name, hospital_id, admin_name, email, password]):
        return html.Div("All fields except address are required.", className="login-error")
    result, err = api.signup(hospital_id.strip(), name, address or "", admin_name, email, password)
    if result:
        return html.Div(f"Registered! Your ID: {hospital_id.strip()}. You can now log in.",
                        className="alert-success", style={"marginTop": "8px"})
    return html.Div(err or "Registration failed. ID may already exist or server is unreachable.",
                    className="login-error", style={"marginTop": "8px"})

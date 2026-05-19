import base64

import dash
from dash import dcc, html, callback, clientside_callback, ClientsideFunction, Input, Output, State
import api

dash.register_page(__name__, path="/settings", title="Settings — Central Link")


def layout():
    blueprint_url = api.get_blueprint()

    return html.Div([
        # Fetch live settings from API
        dcc.Store(id="settings-editing", data=False),

        html.Div(
            style={"display":"flex","justifyContent":"space-between",
                   "alignItems":"center","marginBottom":"28px"},
            children=[
                html.Div("System Settings", className="page-title"),
                html.Div(style={"display":"flex","gap":"10px"}, children=[
                    html.Button("Edit", id="edit-settings-btn",
                                n_clicks=0, className="btn-outline"),
                    html.Button("Save Changes", id="update-settings-btn",
                                n_clicks=0, className="btn-primary",
                                disabled=True,
                                style={"opacity":"0.4","cursor":"not-allowed"}),
                ]),
            ],
        ),
        html.Div(id="settings-save-msg", style={"marginBottom":"16px"}),

        # Hospital Profile
        html.Div(className="cl-card", style={"marginBottom":"20px"}, children=[
            html.Div("Hospital Profile",
                     style={"fontSize":"16px","fontWeight":700,"marginBottom":"4px"}),
            html.Div("Click Edit to modify your facility details.",
                     style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
            html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr",
                            "gap":"16px","marginBottom":"16px"}, children=[
                html.Div([html.Div("Hospital Name", className="cl-label"),
                          dcc.Input(id="set-hosp-name", type="text", className="cl-input",
                                    disabled=True,
                                    style={"opacity":".6","cursor":"not-allowed"})]),
                html.Div([html.Div("Facility ID", className="cl-label"),
                          dcc.Input(id="set-facility-id", type="text", className="cl-input",
                                    disabled=True,
                                    style={"opacity":".6","cursor":"not-allowed"})]),
            ]),
            html.Div([html.Div("Primary Address", className="cl-label"),
                      dcc.Input(id="set-address", type="text", className="cl-input",
                                disabled=True,
                                style={"opacity":".6","cursor":"not-allowed"})]),
        ]),

        # Admin Information
        html.Div(className="cl-card", style={"marginBottom":"20px"}, children=[
            html.Div("Admin Information",
                     style={"fontSize":"16px","fontWeight":700,"marginBottom":"4px"}),
            html.Div("Click Edit to update contact information.",
                     style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
            html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px"}, children=[
                html.Div([html.Div("Full Name", className="cl-label"),
                          dcc.Input(id="set-admin-name", type="text", className="cl-input",
                                    disabled=True,
                                    style={"opacity":".6","cursor":"not-allowed"})]),
                html.Div([html.Div("Email Address", className="cl-label"),
                          dcc.Input(id="set-admin-email", type="email", className="cl-input",
                                    disabled=True,
                                    style={"opacity":".6","cursor":"not-allowed"})]),
            ]),
        ]),

        # Blueprint
        html.Div(className="cl-card", style={"marginBottom":"20px"}, children=[
            html.Div("Clinic Blueprint", style={"fontSize":"16px","fontWeight":700,"marginBottom":"4px"}),
            html.Div("Upload or update the floor plan used for router positioning.",
                     style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
            html.Div(id="blueprint-preview", style={"marginBottom":"16px"}, children=[
                html.Img(src=blueprint_url, style={"maxWidth":"100%","borderRadius":"8px",
                                                    "border":"1px solid var(--border)"})
                if blueprint_url else
                html.Div(style={"width":"100%","height":"120px",
                                "background":"#21262d","border":"1px dashed var(--border)",
                                "borderRadius":"8px","display":"flex","alignItems":"center",
                                "justifyContent":"center","color":"var(--text-muted)",
                                "fontSize":"13px"},
                         children="No blueprint uploaded yet"),
            ]),
            html.Div(id="blueprint-msg", style={"marginBottom":"8px"}),
            html.Div(style={"display":"flex","gap":"8px"}, children=[
                dcc.Upload(id="blueprint-upload",
                           children=html.Button("↑ Upload Blueprint",
                                                className="btn-outline",
                                                style={"fontSize":"12px"}),
                           accept="image/*"),
                html.Button("View Full Map", id="view-blueprint-btn",
                            className="btn-outline", style={"fontSize":"12px"},
                            disabled=not blueprint_url),
            ]),
        ]),

        # BLE Scanner Authorization
        html.Div(className="cl-card", style={"marginBottom":"20px"}, children=[
            html.Div("BLE Scanner Device",
                     style={"fontSize":"16px","fontWeight":700,"marginBottom":"4px"}),
            html.Div("Authorize the USB scanner once so the Scan buttons on Device Management "
                     "and Patient Tracking work without showing a port picker every time.",
                     style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
            html.Div(style={"display":"flex","alignItems":"center","gap":"12px"}, children=[
                html.Button("Authorize Scanner", id="authorize-scanner-btn",
                            n_clicks=0, className="btn-primary",
                            style={"fontSize":"13px"}),
                html.Div(id="scanner-auth-status",
                         style={"fontSize":"12px","color":"var(--text-muted)"},
                         children="Not yet authorized — click to pick your ESP32 serial port."),
            ]),
        ]),

        # Password Reset
        html.Div(className="cl-card", style={"marginBottom":"20px"}, children=[
            html.Div("Password Reset", style={"fontSize":"16px","fontWeight":700,"marginBottom":"4px"}),
            html.Div("Ensure your account security by updating your password periodically.",
                     style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"20px"}),
            html.Div(style={"display":"grid","gridTemplateColumns":"repeat(3,1fr)","gap":"16px"}, children=[
                html.Div([html.Div("Current Password", className="cl-label"),
                          dcc.Input(id="set-cur-pw", type="password", className="cl-input",
                                    placeholder="••••••••")]),
                html.Div([html.Div("New Password", className="cl-label"),
                          dcc.Input(id="set-new-pw", type="password", className="cl-input",
                                    placeholder="••••••••")]),
                html.Div([html.Div("Confirm New Password", className="cl-label"),
                          dcc.Input(id="set-confirm-pw", type="password", className="cl-input",
                                    placeholder="••••••••")]),
            ]),
            html.Div(id="pw-msg", style={"marginTop":"10px"}),
            html.Button("Update Password", id="update-pw-btn", n_clicks=0,
                        className="btn-primary", style={"marginTop":"14px"}),
        ]),

        # Data Management
        html.Div(className="cl-card", style={"marginBottom":"20px"}, children=[
            html.Div("Data Management",
                     style={"fontSize":"16px","fontWeight":700,"marginBottom":"4px"}),
            html.Div("Manage hospital patient records and tracking data.",
                     style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"16px"}),
            html.Div(
                style={"background":"rgba(210,153,34,.08)","border":"1px solid rgba(210,153,34,.25)",
                       "borderRadius":"8px","padding":"14px 16px",
                       "display":"flex","justifyContent":"space-between","alignItems":"center"},
                children=[
                    html.Div([
                        html.Div("Reset Patient Records",
                                 style={"fontWeight":600,"color":"var(--yellow)","marginBottom":"2px"}),
                        html.Div("Removes all patient sessions and records. Routers and devices are kept.",
                                 style={"fontSize":"12px","color":"var(--text-muted)"}),
                    ]),
                    html.Button("Reset Records", id="reset-records-btn", n_clicks=0,
                                className="btn-outline",
                                style={"borderColor":"var(--yellow)","color":"var(--yellow)",
                                       "fontSize":"12px"}),
                ],
            ),
            html.Div(id="reset-records-msg", style={"marginTop":"10px"}),
        ]),

        # Account Management
        html.Div(className="cl-card", children=[
            html.Div("Account Management",
                     style={"fontSize":"16px","fontWeight":700,"color":"var(--red)","marginBottom":"4px"}),
            html.Div("Irreversible actions regarding your system access.",
                     style={"fontSize":"12px","color":"var(--text-muted)","marginBottom":"16px"}),
            html.Div(
                style={"background":"rgba(248,81,73,.08)","border":"1px solid rgba(248,81,73,.25)",
                       "borderRadius":"8px","padding":"14px 16px",
                       "display":"flex","justifyContent":"space-between","alignItems":"center"},
                children=[
                    html.Div([
                        html.Div("Delete Administrator Account",
                                 style={"fontWeight":600,"color":"var(--red)","marginBottom":"2px"}),
                        html.Div("Once deleted, you will lose all access to the management console.",
                                 style={"fontSize":"12px","color":"var(--text-muted)"}),
                    ]),
                    html.Button("Delete Account", id="delete-account-btn", n_clicks=0,
                                className="btn-danger"),
                ],
            ),
            html.Div(id="delete-account-msg", style={"marginTop":"10px"}),
        ]),

        dcc.Store(id="settings-loaded"),
    ])


@callback(
    Output("set-hosp-name",   "value"),
    Output("set-facility-id", "value"),
    Output("set-address",     "value"),
    Output("set-admin-name",  "value"),
    Output("set-admin-email", "value"),
    Input("session-store", "data"),
)
def populate_settings(session):
    s = api.get_settings() or {}
    if s:
        return (
            s.get("NAME", "") or s.get("name", ""),
            s.get("HOSPITAL_ID", "") or s.get("hospital_id", ""),
            s.get("ADDRESS", "") or s.get("address", ""),
            s.get("ADMIN_NAME", "") or s.get("admin_name", ""),
            s.get("ADMIN_EMAIL", "") or s.get("admin_email", ""),
        )
    # Fall back to session if API unavailable
    if not session:
        return "", "", "", "", ""
    return (
        session.get("name", ""),
        session.get("hospital_id", ""),
        session.get("address", ""),
        session.get("admin_name", ""),
        session.get("admin_email", ""),
    )


@callback(
    Output("set-hosp-name",      "disabled"),
    Output("set-address",        "disabled"),
    Output("set-admin-name",     "disabled"),
    Output("set-admin-email",    "disabled"),
    Output("set-hosp-name",      "style"),
    Output("set-address",        "style"),
    Output("set-admin-name",     "style"),
    Output("set-admin-email",    "style"),
    Output("update-settings-btn","disabled"),
    Output("update-settings-btn","style"),
    Output("edit-settings-btn",  "children"),
    Output("settings-editing",   "data"),
    Input("edit-settings-btn",   "n_clicks"),
    State("settings-editing",    "data"),
    prevent_initial_call=True,
)
def toggle_edit(n, currently_editing):
    editing = not currently_editing
    locked  = {"opacity": ".6", "cursor": "not-allowed"}
    active  = {}
    save_locked = {"opacity": "0.4", "cursor": "not-allowed"}
    save_active = {}
    if editing:
        return (False, False, False, False,
                active, active, active, active,
                False, save_active, "Cancel", True)
    else:
        return (True, True, True, True,
                locked, locked, locked, locked,
                True, save_locked, "Edit", False)


@callback(
    Output("settings-save-msg",    "children"),
    Output("set-hosp-name",        "disabled",   allow_duplicate=True),
    Output("set-address",          "disabled",   allow_duplicate=True),
    Output("set-admin-name",       "disabled",   allow_duplicate=True),
    Output("set-admin-email",      "disabled",   allow_duplicate=True),
    Output("set-hosp-name",        "style",      allow_duplicate=True),
    Output("set-address",          "style",      allow_duplicate=True),
    Output("set-admin-name",       "style",      allow_duplicate=True),
    Output("set-admin-email",      "style",      allow_duplicate=True),
    Output("update-settings-btn",  "disabled",   allow_duplicate=True),
    Output("update-settings-btn",  "style",      allow_duplicate=True),
    Output("edit-settings-btn",    "children",   allow_duplicate=True),
    Output("settings-editing",     "data",       allow_duplicate=True),
    Input("update-settings-btn", "n_clicks"),
    State("set-hosp-name",   "value"),
    State("set-address",     "value"),
    State("set-admin-name",  "value"),
    State("set-admin-email", "value"),
    prevent_initial_call=True,
)
def save_settings(n, name, address, admin_name, admin_email):
    if not n:
        return (dash.no_update,) * 13
    ok = api.update_settings_api(name=name, address=address,
                                  admin_name=admin_name, admin_email=admin_email)
    msg = html.Div("Settings saved successfully." if ok else "Failed to save settings.",
                   className="alert-success" if ok else "alert-error")
    if ok:
        locked = {"opacity": ".6", "cursor": "not-allowed"}
        save_locked = {"opacity": "0.4", "cursor": "not-allowed"}
        return (msg, True, True, True, True,
                locked, locked, locked, locked,
                True, save_locked, "Edit", False)
    return (msg,) + (dash.no_update,) * 12


@callback(
    Output("pw-msg", "children"),
    Input("update-pw-btn", "n_clicks"),
    State("set-cur-pw",     "value"),
    State("set-new-pw",     "value"),
    State("set-confirm-pw", "value"),
    prevent_initial_call=True,
)
def update_password(n, cur, new, confirm):
    if not n:
        return dash.no_update
    if not cur or not new or not confirm:
        return html.Div("All password fields are required.", className="alert-error")
    if new != confirm:
        return html.Div("New passwords do not match.", className="alert-error")
    ok = api.update_settings_api(password=new)
    return html.Div("Password updated." if ok else "Failed to update password.",
                    className="alert-success" if ok else "alert-error")


@callback(
    Output("blueprint-msg",     "children"),
    Output("blueprint-preview", "children"),
    Input("blueprint-upload", "contents"),
    State("blueprint-upload", "filename"),
    prevent_initial_call=True,
)
def upload_blueprint(contents, filename):
    if not contents:
        return dash.no_update, dash.no_update
    header, encoded = contents.split(",", 1)
    file_bytes = base64.b64decode(encoded)
    ok = api.upload_blueprint(file_bytes, filename or "blueprint.png")
    if ok:
        new_url = api.get_blueprint()
        preview = (html.Img(src=new_url, style={"maxWidth":"100%","borderRadius":"8px",
                                                 "border":"1px solid var(--border)"})
                   if new_url else
                   html.Div("Blueprint uploaded.", style={"color":"var(--green)"}))
        return html.Div(f"Blueprint '{filename}' uploaded successfully.",
                        className="alert-success"), preview
    return html.Div("Failed to upload blueprint.", className="alert-error"), dash.no_update


@callback(
    Output("reset-records-msg", "children"),
    Input("reset-records-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_records(n):
    if not n:
        return dash.no_update
    ok = api.delete_records()
    return html.Div("All patient records have been reset." if ok else "Failed to reset records.",
                    className="alert-success" if ok else "alert-error")


clientside_callback(
    ClientsideFunction(namespace="serial", function_name="authorize"),
    Output("scanner-auth-status", "children"),
    Input("authorize-scanner-btn", "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output("scanner-auth-status", "children", allow_duplicate=True),
    Input("scanner-auth-status",  "children"),
    prevent_initial_call=True,
)
def _style_auth_status(msg):
    if msg == "ok":
        return html.Span(
            "✓ Scanner authorized — Scan buttons will connect automatically.",
            style={"color": "var(--green)", "fontSize": "12px"},
        )
    return msg


@callback(
    Output("delete-account-msg", "children"),
    Output("session-store",      "data", allow_duplicate=True),
    Output("url",                "pathname", allow_duplicate=True),
    Input("delete-account-btn", "n_clicks"),
    prevent_initial_call=True,
)
def delete_account(n):
    if not n:
        return dash.no_update, dash.no_update, dash.no_update
    ok = api.delete_account()
    if ok:
        api.set_token(None)
        return (html.Div("Account deleted. Redirecting...", className="alert-error"),
                None, "/login")
    return html.Div("Failed to delete account.", className="alert-error"), dash.no_update, dash.no_update

"""Vector floor-plan drawing shared by dashboard, router management, and patient tracking."""

WALL  = "#58a6ff"               # bright blueprint blue for walls
FILL  = "rgba(22, 34, 60, 0.9)" # outer shell fill
ROOM  = "rgba(18, 28, 52, 0.95)"# room interior (slightly lighter than bg)
OPEN  = "rgba(14, 22, 44, 0.7)" # lobby open area
FURN  = "#388bfd"               # furniture outline
FPAD  = "rgba(30, 54, 100, 0.9)"# furniture fill
LABEL = "#79c0ff"               # room label text


def _r(fig, x0, y0, x1, y1, fill=ROOM, lw=2.0, lc=WALL):
    fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                  line=dict(color=lc, width=lw), fillcolor=fill, layer="below")


def _l(fig, x0, y0, x1, y1, lw=2.0):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                  line=dict(color=WALL, width=lw), layer="below")


def _f(fig, x0, y0, x1, y1, lw=1.2):
    fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                  line=dict(color=FURN, width=lw), fillcolor=FPAD, layer="below")


def _t(fig, x, y, text, size=7):
    fig.add_annotation(x=x, y=y, text=text, showarrow=False,
                       font=dict(size=size, color=LABEL),
                       xanchor="center", yanchor="middle")


def draw_clinic(fig):
    """
    Layout (normalized 0-1 coords):
    ┌───────────┬────────────┬───────────┐  y=0.97
    │           │  EXAM 1   │  EXAM 2   │
    │  LOBBY /  ├────────────┼───────────┤  y=0.63
    │  WAITING  │  WARD 1   │  WARD 2   │
    │           ├────────────┼───────────┤  y=0.33
    │           │   NURSE   │  STORAGE  │
    └───────────┴────────────┴───────────┘  y=0.03
    x:  0.03   0.38        0.68         0.97
    """

    # ── Outer shell ──────────────────────────────────────────────────
    _r(fig, 0.03, 0.03, 0.97, 0.97, fill=FILL, lw=2.5)

    # ── Left open area (lobby) ────────────────────────────────────────
    _r(fig, 0.03, 0.03, 0.38, 0.97, fill=OPEN, lw=0, lc=WALL)
    _t(fig, 0.205, 0.60, "LOBBY", size=10)
    _t(fig, 0.205, 0.52, "WAITING AREA", size=8)
    # Reception desk
    _f(fig, 0.07, 0.83, 0.33, 0.91)
    # Waiting chairs
    for cx in [0.07, 0.16, 0.25]:
        _f(fig, cx, 0.08, cx + 0.07, 0.15)

    # ── Main vertical dividing wall (door gap y=0.20–0.28) ───────────
    _l(fig, 0.38, 0.03, 0.38, 0.20)
    _l(fig, 0.38, 0.28, 0.38, 0.97)

    # ── Top/middle boundary y=0.63 (door gap x=0.60–0.72) ────────────
    _l(fig, 0.38, 0.63, 0.60, 0.63)
    _l(fig, 0.72, 0.63, 0.97, 0.63)

    # ── Middle/bottom boundary y=0.33 (door gap x=0.58–0.70) ─────────
    _l(fig, 0.38, 0.33, 0.58, 0.33)
    _l(fig, 0.70, 0.33, 0.97, 0.33)

    # ── Vertical room divider x=0.68 ─────────────────────────────────
    _l(fig, 0.68, 0.63, 0.68, 0.97)          # top solid
    _l(fig, 0.68, 0.33, 0.68, 0.45)          # middle lower
    _l(fig, 0.68, 0.52, 0.68, 0.63)          # middle upper
    _l(fig, 0.68, 0.03, 0.68, 0.18)          # bottom lower
    _l(fig, 0.68, 0.26, 0.68, 0.33)          # bottom upper

    # ── EXAM ROOM 1 ───────────────────────────────────────────────────
    _t(fig, 0.53, 0.94, "EXAM ROOM 1", size=7)
    _f(fig, 0.41, 0.87, 0.65, 0.91)          # counter
    _f(fig, 0.43, 0.70, 0.61, 0.83)          # exam table
    _f(fig, 0.62, 0.72, 0.65, 0.79)          # stool

    # ── EXAM ROOM 2 ───────────────────────────────────────────────────
    _t(fig, 0.825, 0.94, "EXAM ROOM 2", size=7)
    _f(fig, 0.71, 0.87, 0.94, 0.91)
    _f(fig, 0.73, 0.70, 0.91, 0.83)
    _f(fig, 0.92, 0.72, 0.94, 0.79)

    # ── WARD 1 — 3 beds ───────────────────────────────────────────────
    _t(fig, 0.53, 0.61, "WARD 1", size=7)
    for bx, bw in [(0.41, 0.07), (0.50, 0.07), (0.59, 0.07)]:
        _f(fig, bx, 0.38, bx + bw, 0.59)
        _f(fig, bx + 0.005, 0.56, bx + bw - 0.005, 0.59)   # pillow

    # ── WARD 2 — 2 beds ───────────────────────────────────────────────
    _t(fig, 0.825, 0.61, "WARD 2", size=7)
    for bx, bw in [(0.71, 0.10), (0.84, 0.10)]:
        _f(fig, bx, 0.38, bx + bw, 0.59)
        _f(fig, bx + 0.005, 0.56, bx + bw - 0.005, 0.59)

    # ── NURSE STATION ─────────────────────────────────────────────────
    _t(fig, 0.53, 0.31, "NURSE STATION", size=7)
    _f(fig, 0.41, 0.14, 0.64, 0.19)          # front counter
    _f(fig, 0.41, 0.19, 0.45, 0.28)          # left wing
    _f(fig, 0.60, 0.19, 0.64, 0.28)          # right wing

    # ── STORAGE ───────────────────────────────────────────────────────
    _t(fig, 0.825, 0.31, "STORAGE", size=7)
    _f(fig, 0.71, 0.06, 0.94, 0.13)
    _f(fig, 0.71, 0.16, 0.94, 0.23)

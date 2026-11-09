"""Famicom (HVC) cartridge shell geometry for the board generator, in board coordinates (mm):
x = 0..90 left to right seen from the FRONT (pins 1-30 side, pin 1 on the left), y = 0 at the top edge, increasing
toward the card edge; the card-edge shoulder (tab base) is at y = body_h. h = body_h - y is the height above the shoulder.

Sources (see docs/04_hardware.md, "基板外形の訂正"):
  * HVC-TGROM-01 (standard / small shell): nesdev "Famicom cartridge dimensions" table (A 90, A.2 81, A.2.1 43, A.2.2 33,
    B 46.1, B.1 23.2, B.2 20.9, B.3 10.7) and the KiCad footprint it links to (Gumball2415 NES-Famicom-Cartridge-PCBs,
    common_footprints.pretty/HVC-TGROM-01.kicad_mod): body 46.1 mm ABOVE the shoulder, side notches 4.5 x 2.0 at
    h 23.2-25.2, slot x' 2.5..7.5 (x' = x - 45) in the same band. B.1 + 2.0 + B.2 = 46.1 and 43 + 5 + 33 = 81 confirm it.
  * HVC-ExROM (Nintendo large shell, also Koei / Enix / Square large carts, and the Muramasa / kadenken "でかカセット"
    reproduction shell): HVC-ETROM-01.kicad_mod from the same repository plus three reproduction boards (YARN, Infinest
    Lagrange-Point-PCB, OSH Park gj7wJWmV); the outline below is the conservative envelope of the four (research notes
    in docs/10_rev_f_board.md).
  * Courtyards drawn in those footprints mark where Nintendo boards keep components away (shell ribs / posts). They are
    used as component keep-outs; tracks may pass under them (solder mask).
All margins added here make the board SMALLER than the reference (more clearance)."""

TAB_X0, TAB_X1 = 5.8, 84.2          # 78.4 mm card-edge tab (unchanged)
W = 90.0

def _rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def _common_keepouts(body_h, notch_lo, notch_hi):
    """Component keep-outs shared by both shells (from the HVC-TGROM-01 / ETROM-01 courtyards), as (side, polygon)."""
    y = lambda h: body_h - h
    ko = []
    # front: full-width rib band at the notch height, rib boxes around the notches and around the slot
    ko.append(('F', _rect(45 - 40.7, y(notch_hi + 0.2), 45 + 40.7, y(notch_lo - 0.2))))
    for x0, x1 in ((45 - 42.2, 45 - 40.3), (45 + 40.3, 45 + 42.2), (45 + 3.8, 45 + 6.2)):
        ko.append(('F', _rect(x0, y(27.25), x1, y(21.15))))
    ko.append(('F', _rect(45 - 1.2, y(39.45 + 1.2), 45 + 1.2, y(39.45 - 1.2))))          # O2 post at (0, 39.45)
    # back: two O2 posts at (+-31.75, 21.45); no module may bridge the slot hole (+0.5 mm) in case a shell feature
    # comes through it (the reference marks nothing there on the back)
    for xc in (45 - 31.75, 45 + 31.75):
        ko.append(('B', _rect(xc - 1.2, y(21.45 + 1.2), xc + 1.2, y(21.45 - 1.2))))
    return ko

def hvc_small():
    """Standard Famicom shell: HVC-TGROM-01 outline (90 x 46.1 body + 10.7 tab = 56.8 mm)."""
    H = 46.1
    y = lambda h: H - h
    lo, hi = 23.0, 25.4                  # notch / slot band, 0.2 mm larger than the reference 23.2-25.2 each way
    nx = 4.7                             # notch depth (reference 4.5)
    body = [(TAB_X0, H), (0, H), (0, y(lo)), (nx, y(lo)), (nx, y(hi)), (0, y(hi)), (0, 0),
            (W, 0), (W, y(hi)), (W - nx, y(hi)), (W - nx, y(lo)), (W, y(lo)), (W, H), (TAB_X1, H)]
    slot = _rect(45 + 2.3, y(hi), 45 + 7.7, y(lo))
    route_ko = [_rect(-1, y(hi) - 0.4, nx + 0.4, y(lo) + 0.4), _rect(W - nx - 0.4, y(hi) - 0.4, W + 1, y(lo) + 0.4),
                _rect(45 + 2.3 - 0.4, y(hi) - 0.4, 45 + 7.7 + 0.4, y(lo) + 0.4)]
    ko = _common_keepouts(H, 23.2, 25.2) + [('B', _rect(45 + 2.3 - 0.5, y(hi + 0.5), 45 + 7.7 + 0.5, y(lo - 0.5)))]
    return dict(name='HVC small (TGROM-01)', body_h=H, outline_body=body, cutouts=[slot],
                route_keepouts=route_ko, comp_keepouts=ko)

def hvc_large(H=75.0):
    """Nintendo large shell (HVC-ExROM family), conservative envelope; straight top up to h 75.0 (the shell's upper
    corner bosses start above h 75.1, so they are never touched)."""
    assert H <= 75.0
    y = lambda h: H - h
    body = [(TAB_X0, H), (45 - 43.4, H), (45 - 43.4, y(6.7)), (0, y(6.7)), (0, y(18.7)), (0.2, y(18.7)), (0.2, y(22.8)),
            (45 - 40.25, y(22.8)), (45 - 40.25, y(25.2)), (0, y(25.2)), (0, 0),
            (W, 0), (W, y(25.2)), (45 + 40.25, y(25.2)), (45 + 40.25, y(22.8)), (W - 0.2, y(22.8)), (W - 0.2, y(18.7)),
            (W, y(18.7)), (W, y(6.7)), (45 + 43.4, y(6.7)), (45 + 43.4, H), (TAB_X1, H)]
    slot = _rect(45 + 2.35, y(25.2), 45 + 7.75, y(22.8))
    route_ko = [_rect(-1, y(25.2) - 0.4, 45 - 40.25 + 0.4, y(22.8) + 0.4), _rect(45 + 40.25 - 0.4, y(25.2) - 0.4, W + 1, y(22.8) + 0.4),
                _rect(-1, y(22.8), 0.6, y(18.7)), _rect(W - 0.6, y(22.8), W + 1, y(18.7)),
                _rect(-1, y(6.7) - 0.4, 45 - 43.4 + 0.4, H + 1), _rect(45 + 43.4 - 0.4, y(6.7) - 0.4, W + 1, H + 1),
                _rect(45 + 2.35 - 0.4, y(25.2) - 0.4, 45 + 7.75 + 0.4, y(22.8) + 0.4)]
    ko = _common_keepouts(H, 22.8, 25.2) + [('B', _rect(45 + 2.35 - 0.5, y(25.2 + 0.5), 45 + 7.75 + 0.5, y(22.8 - 0.5)))]
    for x0, x1 in ((45 - 45.5, 45 - 41.3), (45 + 41.3, 45 + 45.5)):                     # front ribs near the lower bosses
        ko.append(('F', _rect(x0, y(3.55), x1, y(1.65))))
    return dict(name='HVC large (ExROM)', body_h=H, outline_body=body, cutouts=[slot],
                route_keepouts=route_ko, comp_keepouts=ko)

def rect_body(body_h):
    """Plain rectangle (rev A-F, kept for regenerating old revisions)."""
    return dict(name='rectangle', body_h=body_h, outline_body=[(TAB_X0, body_h), (0, body_h), (0, 0), (W, 0), (W, body_h), (TAB_X1, body_h)],
                cutouts=[], route_keepouts=[], comp_keepouts=[])

"""
EQsimu problem: the physics a compset defines once for every code.

A compset's user_defined_params.py does `par = problem()`, sets the fields
below, puts code-specific settings in par.eqquasi / par.eqdyna, and defines
fault(p, x, z). utils/convert.py turns it into each code's own
user_defined_params.py; see SHARED in convert.py for which field goes where.
"""

class problem:
    mode = 2                 # 2: earthquake cycle
    istart, iend = 1, 1      # cycle ids to run (EQquasi)

    # Fault: vertical strike-slip, in the xz plane (y = 0), m.
    fxmin, fxmax = None, None
    fzmin, fzmax = None, None
    dx = None                # on-fault grid spacing, m
    ntotft = 1
    roughness = None         # fault surface, see utils/roughness.py;
                             # None means a planar fault

    # Elastic material.
    vp, vs, rou = None, None, None

    # Friction (rate-and-state) and loading.
    friclaw = 3              # rsf_aging(3)
    fric_rsf_a = fric_rsf_b = fric_rsf_Dc = None
    fric_rsf_deltaa = None
    fric_rsf_r0 = fric_rsf_v0 = None
    init_norm = None         # Pa, negative compressive
    creep_slip_rate = None   # m/s

    nt_out = 20              # output every nt_out steps

    # Box that is handed from the cycle code to the dynamic code, m.
    xmin_trans = xmax_trans = zmin_trans = None
    ymin_trans = ymax_trans = None
    dx_trans = None

    # Code-specific settings, written verbatim (names as each code spells them).
    eqquasi = {}
    eqdyna = {}

    # fault(p, x, z) -> dict of on-fault initial values at (x, z), with keys
    # a, b, Dc, v0, f0, vini, tnrm, tstk, state. p holds the fields above.
    fault = None

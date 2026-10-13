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
    # ntotft == 1 (default): fxmin/fxmax/fzmin/fzmax are that one fault's
    # box directly, and leave faultgeom None.
    # ntotft > 1 (stepover): leave fxmin/fxmax/fzmin/fzmax None and instead
    # set faultgeom to a list of ntotft (fxmin, fxmax, ycoor, fzmin, fzmax)
    # tuples, m, one per fault (EQquasi's own on-disk convention). convert.py
    # derives fxmin/fxmax/fzmin/fzmax from it (fault 1's own box, which is
    # what EQdyna's legacy single-fault fields need) and EQquasi's own union
    # box, and checks every fault bound and the y stepover offset lands on a
    # whole-dx grid node from the union origin -- both codes' mesh
    # generators assume this. Roughness is not supported at ntotft > 1
    # (EQdyna refuses rough input combined with multiple faults): the
    # problem's fault must be planar.
    fxmin, fxmax = None, None
    fzmin, fzmax = None, None
    faultgeom = None
    dx = None                # on-fault grid spacing, m
    ntotft = 1
    roughness = None         # fault surface, see utils/roughness.py;
                             # None means a planar fault (required if
                             # ntotft > 1)

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
    # ntotft > 1: fault may instead take a 4th argument, fault(p, x, z, ift),
    # the 0-based fault index, for per-fault physics; convert.py detects the
    # arity and calls accordingly.
    fault = None

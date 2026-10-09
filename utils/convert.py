"""
Convert an EQsimu compset (one problem) into the user_defined_params.py that
EQquasi and EQdyna each read. This file is the EQsimu API to the codes: it is
the only place that knows their parameter names and on-fault array layouts,
and it checks every name against the code's defaultParameters at the pinned
commit, so a renamed parameter fails here instead of being silently dropped.
"""
import contextlib
import importlib.util
import inspect
import io
import os
import sys

UTILS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, UTILS)
import roughness

# Problem fields written to each code under the same name.
COMMON = ["mode", "fxmin", "fxmax", "fzmin", "fzmax", "dx", "ntotft",
          "vp", "vs", "rou", "friclaw", "init_norm", "creep_slip_rate",
          "fric_rsf_a", "fric_rsf_b", "fric_rsf_Dc", "fric_rsf_deltaa",
          "fric_rsf_r0", "fric_rsf_v0", "nt_out",
          "xmin_trans", "xmax_trans", "zmin_trans", "ymin_trans", "ymax_trans",
          "dx_trans"]
SHARED = {"eqquasi": COMMON + ["istart", "iend"], "eqdyna": COMMON}

# fault() keys -> on-fault array index in each code.
EQQUASI_INDEX = dict(a="FR_RSF_A", b="FR_RSF_B", Dc="FR_RSF_DC",
                     v0="FR_RSF_V0", f0="FR_RSF_F0", vini="FR_VINIT",
                     state="FR_STATE", tnrm="FR_TNRM0", tstk="FR_TSTK0")
EQDYNA_INDEX = dict(a=9, b=10, Dc=11, v0=12, f0=13, vini=46,
                    state=20, tnrm=7, tstk=8)
# In mode 2 EQdyna takes stress and state from the EQquasi restart.
EQDYNA_FROM_RESTART = ("tnrm", "tstk", "state")

ROOT_ENV = {"eqquasi": "EQQUASIROOT", "eqdyna": "EQDYNAROOT"}
COMPSET_DIR = {"eqquasi": "compset", "eqdyna": "case_input"}

# Multi-fault (ntotft > 1): par.eqdyna may set these; EQdyna's case.setup
# reads them with getattr (lib.py's resolveFaultGeom/resolveOnFaultVarsPerFault/
# resolveOnFaultStationsPerFault), so they are never declared as a class
# attribute in defaultParameters.py and would otherwise fail the known-
# parameter check in _settings. faultgeom/onFaultVarsPerFault are written
# directly by render() below (never through par.eqdyna), so only the
# per-fault station list needs the allowance.
EXTRA_KNOWN = {"eqquasi": set(), "eqdyna": {"st_coor_on_fault_per_fault"}}


class ConvertError(Exception):
    pass


def _load(path, name, extra_path=()):
    sys.path[:0] = list(extra_path)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(mod)
    finally:
        del sys.path[:len(extra_path)]
    return mod


def _resolve_faultgeom(par, compset_dir):
    """ntotft > 1: validate par.faultgeom and derive fxmin/fxmax/fzmin/fzmax
    (fault 1's own box -- EQdyna's legacy single-fault fields; identical
    meaning to the ntotft == 1 case). Returns the union
    (fxmin, fxmax, fzmin, fzmax) across every fault, which EQquasi's own
    box needs instead (see render()). No silent rounding (rule 5): every
    fault bound and the y stepover offset must land on a whole multiple of
    dx from the union origin, or this raises."""
    geom = par.faultgeom
    if geom is None:
        if par.ntotft > 1:
            raise ConvertError(
                f"{compset_dir}: par.ntotft = {par.ntotft} but par.faultgeom "
                "is not set; give one (fxmin, fxmax, ycoor, fzmin, fzmax) "
                "tuple per fault")
        return None
    if par.ntotft == 1:
        raise ConvertError(f"{compset_dir}: par.faultgeom is set but "
                           "par.ntotft == 1; set par.ntotft to the number "
                           "of faults")
    if len(geom) != par.ntotft:
        raise ConvertError(f"{compset_dir}: par.faultgeom has {len(geom)} "
                           f"entries but par.ntotft = {par.ntotft}")
    if par.roughness is not None:
        raise ConvertError(
            f"{compset_dir}: par.ntotft = {par.ntotft} with par.roughness "
            "set; EQdyna refuses rough-surface input combined with "
            "multiple faults, so a multi-fault problem's fault must be "
            "planar (par.roughness = None)")
    if (par.fxmin, par.fxmax, par.fzmin, par.fzmax) != (None, None, None, None):
        raise ConvertError(
            f"{compset_dir}: par.faultgeom is set; par.fxmin/fxmax/fzmin/"
            "fzmax are derived from it (fault 1's own box) and must be "
            "left unset (None)")

    fxmin_u = min(f[0] for f in geom)
    fxmax_u = max(f[1] for f in geom)
    fzmin_u = min(f[3] for f in geom)
    fzmax_u = max(f[4] for f in geom)
    y0, dx = geom[0][2], par.dx

    def _check(val, origin, label):
        off = (val - origin)/dx
        if abs(off - round(off)) > 1e-6:
            raise ConvertError(
                f"{compset_dir}: par.faultgeom: {label} = {val} is not a "
                f"whole multiple of dx = {dx} from the union origin "
                f"{origin}; both codes' mesh generators require every "
                "fault bound and the stepover offset to land on a grid "
                "node")

    for i, (xlo, xhi, ycoor, zlo, zhi) in enumerate(geom):
        _check(xlo, fxmin_u, f"fault {i} xlo")
        _check(xhi, fxmin_u, f"fault {i} xhi")
        _check(zlo, fzmin_u, f"fault {i} zlo")
        _check(zhi, fzmin_u, f"fault {i} zhi")
        _check(ycoor, y0, f"fault {i} ycoor (stepover offset)")

    par.fxmin, par.fxmax = geom[0][0], geom[0][1]
    par.fzmin, par.fzmax = geom[0][3], geom[0][4]
    return fxmin_u, fxmax_u, fzmin_u, fzmax_u


def load_problem(compset_dir):
    mod = _load(os.path.join(compset_dir, "user_defined_params.py"),
                "eqsimu_problem", [UTILS])
    par = mod.par
    if not callable(par.fault):
        raise ConvertError(f"{compset_dir}: par.fault is not set")
    par._faultgeom_union = _resolve_faultgeom(par, compset_dir)
    missing = [k for k in sorted(set(SHARED["eqquasi"]) | set(SHARED["eqdyna"]))
               if getattr(par, k) is None]
    if missing:
        raise ConvertError(f"{compset_dir}: unset problem fields: {missing}")
    funcs = sorted((f for f in vars(mod).values()
                    if inspect.isfunction(f) and f.__module__ == mod.__name__),
                   key=lambda f: f.__code__.co_firstlineno)
    return par, funcs


def code_parameters(code):
    root = os.environ.get(ROOT_ENV[code])
    if not root:
        raise ConvertError(f"{ROOT_ENV[code]} is not set; source checkout.sh")
    scripts = os.path.join(root, "scripts")
    return _load(os.path.join(scripts, "defaultParameters.py"),
                 "dp_" + code, [scripts])


def _lit(v, name):
    if isinstance(v, (bool, int, float, str, type(None))):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return repr(v) if all(_lit(x, name) for x in v) else None
    raise ConvertError(f"{name}: cannot write a {type(v).__name__}")


def _settings(par, code, known):
    out = [(k, getattr(par, k)) for k in SHARED[code]]
    out += list(getattr(par, code).items())
    if par.roughness:
        out.append(("rough_fault", 1) if code == "eqquasi"
                   else ("insertFaultType", 3))
    unknown = [k for k, _ in out if k not in known]
    if unknown:
        raise ConvertError(f"{code} has no parameter(s) {unknown}; "
                           f"update utils/convert.py or the compset")
    return out


def _namespace(par):
    fields = sorted(set(SHARED["eqquasi"]) | set(SHARED["eqdyna"]))
    body = ",\n    ".join(f"{k}={_lit(getattr(par, k), k)}" for k in fields)
    return f"p = SimpleNamespace(\n    {body})"


def render(par, funcs, code, source):
    multi = par.ntotft > 1
    dp = code_parameters(code)
    known = {k for k in vars(dp.parameters) if not k.startswith("_")} \
        | EXTRA_KNOWN[code]
    if multi and code == "eqdyna" and "st_coor_on_fault_per_fault" not in par.eqdyna:
        raise ConvertError(
            f"{source}: par.ntotft = {par.ntotft} but par.eqdyna has no "
            "st_coor_on_fault_per_fault (a list of ntotft (x, z) km station "
            "lists, one per fault; EQdyna cannot infer fault ownership from "
            "a flat list)")
    lines = [f"# Generated by EQsimu utils/convert.py from {source}.",
             "# Do not edit: edit the EQsimu compset and recreate the case.",
             "import numpy as np",
             "from math import *",
             "from types import SimpleNamespace",
             "from defaultParameters import *" if code == "eqquasi"
             else "from defaultParameters import parameters",
             "",
             "par = parameters()"]
    lines += [f"par.{k} = {_lit(v, k)}" for k, v in _settings(par, code, known)]
    lines += ["par.dy = par.dx", "par.dz = par.dx"]
    if code == "eqdyna":
        lines += ["if par.nmat == 1:",
                  "    par.roumax, par.vmaxPML = par.rou, par.vp"]
    if multi:
        if code == "eqquasi":
            # EQquasi's own on-disk faultgeom convention: one (fxmin, fxmax,
            # ycoor, fzmin, fzmax) tuple per fault, unchanged from the
            # problem's. par.fxmin/fxmax/fzmin/fzmax (fault 1's box, just
            # written above by _settings/SHARED) are overridden here to the
            # union every one of EQquasi's own uses of them (the host grid,
            # bModelGeometry) needs instead.
            fxmin_u, fxmax_u, fzmin_u, fzmax_u = par._faultgeom_union
            lines += [f"par.faultgeom = {_lit(par.faultgeom, 'faultgeom')}",
                     f"par.fxmin, par.fxmax = {_lit(fxmin_u, 'fxmin')}, "
                     f"{_lit(fxmax_u, 'fxmax')}",
                     f"par.fzmin, par.fzmax = {_lit(fzmin_u, 'fzmin')}, "
                     f"{_lit(fzmax_u, 'fzmax')}"]
        else:
            # EQdyna's own convention: (fxmin, fxmax, fymin, fymax, fzmin,
            # fzmax), fymin == fymax for these vertical faults. fxmin/fxmax/
            # fzmin/fzmax above stay fault 1's own box (already set by
            # _resolve_faultgeom/_settings) -- EQdyna's legacy single-fault
            # fields, read directly by netcdf_write_on_fault_vars for fault 1.
            geom6 = [(xlo, xhi, ycoor, ycoor, zlo, zhi)
                    for xlo, xhi, ycoor, zlo, zhi in par.faultgeom]
            lines.append(f"par.faultgeom = {_lit(geom6, 'faultgeom')}")
    rnd = "int" if code == "eqquasi" else "round"
    lines += [f"par.nfx = {rnd}((par.fxmax - par.fxmin)/par.dx + 1)",
              f"par.nfz = {rnd}((par.fzmax - par.fzmin)/par.dx + 1)",
              "par.fx = np.linspace(par.fxmin, par.fxmax, par.nfx)",
              "par.fz = np.linspace(par.fzmin, par.fzmax, par.nfz)"]
    if multi and code == "eqdyna":
        lines.append("par.n_on_fault = "
                     "sum(len(s) for s in par.st_coor_on_fault_per_fault)")
    else:
        lines.append("par.n_on_fault = len(par.st_coor_on_fault)")
    lines += ["par.n_off_fault = len(par.st_coor_off_fault)",
              "", _namespace(par), ""]
    lines += [inspect.getsource(f) for f in funcs]

    fault_ift = len(inspect.signature(par.fault).parameters) >= 4

    def call(ift_expr):
        return f"fault(p, x, z, {ift_expr})" if fault_ift else "fault(p, x, z)"

    if code == "eqquasi":
        if not multi:
            lines += ["par.on_fault_vars = np.zeros((par.ntotft, par.nfz, par.nfx, 100))",
                      "for ix, x in enumerate(par.fx):",
                      "    for iz, z in enumerate(par.fz):",
                      f"        v = {call('0')}"]
            lines += [f"        par.on_fault_vars[0, iz, ix, {i}] = v[{k!r}]"
                      for k, i in EQQUASI_INDEX.items()]
        else:
            # ntotft > 1: (ntotft, nfzMax, nfxMax, 100), padded to the
            # largest fault's own (nfx, nfz) -- not necessarily the union
            # grid's -- matching EQquasi's own multi-fault convention
            # (case.setup's netcdf_write_on_fault_vars detects this layout
            # from array rank).
            lines += [
                "nfxs = [round((xhi - xlo)/par.dx + 1) "
                "for xlo, xhi, ycoor, zlo, zhi in par.faultgeom]",
                "nfzs = [round((zhi - zlo)/par.dx + 1) "
                "for xlo, xhi, ycoor, zlo, zhi in par.faultgeom]",
                "nfxMax, nfzMax = max(nfxs), max(nfzs)",
                "par.on_fault_vars = np.zeros((par.ntotft, nfzMax, nfxMax, 100))",
                "for ift, (xlo, xhi, ycoor, zlo, zhi) in enumerate(par.faultgeom):",
                "    fx_ift = np.linspace(xlo, xhi, nfxs[ift])",
                "    fz_ift = np.linspace(zlo, zhi, nfzs[ift])",
                "    for ix, x in enumerate(fx_ift):",
                "        for iz, z in enumerate(fz_ift):",
                f"            v = {call('ift')}"]
            lines += [f"            par.on_fault_vars[ift, iz, ix, {i}] = v[{k!r}]"
                      for k, i in EQQUASI_INDEX.items()]
    else:
        keys = {k: i for k, i in EQDYNA_INDEX.items()
                if not (par.mode == 2 and k in EQDYNA_FROM_RESTART)}

        def ofv_body(arr, indent):
            pad = " "*indent
            out = [f"{pad}{arr}[iz, ix, 1] = par.fric_sw_fs",
                   f"{pad}{arr}[iz, ix, 2] = par.fric_sw_fd",
                   f"{pad}{arr}[iz, ix, 3] = par.fric_sw_D0",
                   f"{pad}{arr}[iz, ix, 14] = par.fric_rsf_fw"]
            out += [f"{pad}{arr}[iz, ix, {i}] = v[{k!r}]" for k, i in keys.items()]
            return out

        # Fault 1: legacy top-level par.on_fault_vars/par.fx/par.fz/par.nfx/
        # par.nfz, bit-identical to the ntotft == 1 path (those already hold
        # fault 1's own box at ntotft > 1 -- see _resolve_faultgeom).
        lines += ["par.on_fault_vars = np.zeros((par.nfz, par.nfx, 100))",
                  "for ix, x in enumerate(par.fx):",
                  "    for iz, z in enumerate(par.fz):",
                  f"        v = {call('0')}"]
        lines += ofv_body("par.on_fault_vars", 8)
        if multi:
            # Faults 2..ntotft: each on its own (nfx_i, nfz_i) box.
            lines += [
                "par.onFaultVarsPerFault = [par.on_fault_vars]",
                "for ift in range(1, par.ntotft):",
                "    xlo, xhi, ylo, yhi, zlo, zhi = par.faultgeom[ift]",
                "    nfx_i = round((xhi - xlo)/par.dx + 1)",
                "    nfz_i = round((zhi - zlo)/par.dz + 1)",
                "    fx_i = np.linspace(xlo, xhi, nfx_i)",
                "    fz_i = np.linspace(zlo, zhi, nfz_i)",
                "    arr = np.zeros((nfz_i, nfx_i, 100))",
                "    for ix, x in enumerate(fx_i):",
                "        for iz, z in enumerate(fz_i):",
                f"            v = {call('ift')}"]
            lines += ofv_body("arr", 12)
            lines.append("    par.onFaultVarsPerFault.append(arr)")
    return "\n".join(lines) + "\n"


def write_code_compset(compset_dir, code, out_dir):
    """Write <out_dir>/user_defined_params.py (+ fault geometry) for code."""
    par, funcs = load_problem(compset_dir)
    os.makedirs(out_dir, exist_ok=True)
    text = render(par, funcs, code, os.path.basename(compset_dir.rstrip("/")))
    with open(os.path.join(out_dir, "user_defined_params.py"), "w") as f:
        f.write(text)
    y = roughness.heights(par, compset_dir)
    if y is not None:
        roughness.write(par, y, os.path.join(out_dir, roughness.FILENAME))
    return par


def upstream_compset_arg(code, out_dir):
    """The compset argument that makes code's create.newcase read out_dir."""
    base = os.path.join(os.environ[ROOT_ENV[code]], COMPSET_DIR[code])
    return os.path.relpath(out_dir, base)

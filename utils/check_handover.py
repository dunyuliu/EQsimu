#! /usr/bin/env python3
"""
check_handover.py: validate one fdc handover file BEFORE the receiving code
reads it. Runs in BOTH directions of the fdc chain (utils/case.setup):

  eqquasi_to_eqdyna   fault.r.nc        written by EQquasi, read by EQdyna
                                         (netcdf_read_on_fault_eqdyna_restart)
  eqdyna_to_eqquasi   fault.dyna.r.nc   written by EQdyna,  read by EQquasi
                                         (netcdf_read_on_fault_restart, infile2)

Both codes' restart readers (components/eqquasi/src/netcdf_io.f90,
components/eqdyna/src/fortran/netcdf_io.f90) agree on ONE set of 12
untagged on-fault variable names and units -- this script reads that exact
set, not a guess:

  shear_strike (Pa), shear_dip (Pa), effective_normal (Pa), slip_rate (m/s),
  state_variable (unit), state_normal (Pa),
  vxm, vym, vzm, vxs, vys, vzs (m/s)

Exit nonzero on ANY inconsistency, naming the variable, fault index, and
node index (1-based, matching the Fortran side) that failed. Never a
silent warning, never a count-only message.

Usage:
  check_handover.py --direction {eqquasi_to_eqdyna,eqdyna_to_eqquasi} \\
                     --file PATH --params-dir DIR

--params-dir is the RECEIVING code's own case directory (it has that code's
generated user_defined_params.py on sys.path) -- shape is checked against
the RECEIVER's own expected (nx,nz) fault grid, per code, per fault.
"""
import argparse
import os
import sys

import numpy as np

# The one set of names/units both codes' restart readers agree on (see
# module docstring). Order does not matter; names and units do.
REQUIRED_VARS = {
    "shear_strike": "Pa", "shear_dip": "Pa", "effective_normal": "Pa",
    "slip_rate": "m/s", "state_variable": "unit", "state_normal": "Pa",
    "vxm": "m/s", "vym": "m/s", "vzm": "m/s",
    "vxs": "m/s", "vys": "m/s", "vzs": "m/s",
}
VELOCITY_PAIRS = [("vxm", "vxs"), ("vym", "vys"), ("vzm", "vzs")]

# Below this, a pair (vm, vs) is antisymmetric (vm ~= -vs): EQquasi's known
# bug (PATHWAY_FORWARD.md P2 row, 2026-10-12 owner decision). Above it, the
# pair is consistent with absolute particle velocities (vm ~= vs), which is
# what EQdyna writes and what the project owner says is correct. Measured on
# real bp1001.fdc.rough.250 cycle-0 output: EQquasi's median relative
# residual is ~0.005-0.03, EQdyna's is ~2.0 -- 0.5 sits cleanly between them.
ANTISYM_MEDIAN_THRESHOLD = 0.5

KNOWN_BUG_MSG = (
    "This is the INTENDED, KNOWN-BAD result, not a checker bug: EQdyna "
    "writes absolute particle velocities (correct, per project-owner "
    "decision 2026-10-12); EQquasi currently writes vxm..vzs as "
    "antisymmetric relative half slip rates (vxm ~= -vxs etc), an upstream "
    "EQquasi bug not yet fixed (PATHWAY_FORWARD.md P2 row). This checker "
    "MUST fail on EQquasi's output for this reason until EQquasi is fixed "
    "upstream -- do not 'fix' the checker to pass this case."
)


class HandoverError(SystemExit):
    def __init__(self, msg):
        super().__init__("check_handover.py: FAIL: " + msg)


def load_receiver_par(params_dir):
    """Import user_defined_params.par from params_dir (the receiving code's
    own case directory), without polluting sys.path for anything else.

    user_defined_params.py does `from defaultParameters import *`; both
    codes' own case.setup puts that module (and lib.py) in the case's own
    tool/ directory (scripts/case.setup: sys.path.insert(0, .../tool)), so
    look there too, same as the real run does."""
    extra = [params_dir]
    tool_dir = os.path.join(params_dir, "tool")
    if os.path.isdir(tool_dir):
        extra.append(tool_dir)
    for d in extra:
        sys.path.insert(0, d)
    try:
        import importlib
        if "user_defined_params" in sys.modules:
            del sys.modules["user_defined_params"]
        mod = importlib.import_module("user_defined_params")
        return mod.par
    finally:
        for d in extra:
            sys.path.remove(d)


def fault_boxes(par):
    """[(fxlo, fxhi, fzlo, fzhi), ...] per fault, 1-based fault order,
    exactly the per-fault box both codes' own netcdf_write_on_fault /
    netcdf_read_on_fault_eqdyna_restart derive their (nfx, nfz) from."""
    ntotft = getattr(par, "ntotft", 1)
    if ntotft == 1:
        return [(par.fxmin, par.fxmax, par.fzmin, par.fzmax)]
    boxes = []
    for g in par.faultgeom:
        if len(g) == 5:       # EQquasi: (xlo, xhi, ycoor, zlo, zhi)
            boxes.append((g[0], g[1], g[3], g[4]))
        elif len(g) == 6:     # EQdyna: (xlo, xhi, ylo, yhi, zlo, zhi)
            boxes.append((g[0], g[1], g[4], g[5]))
        else:
            raise HandoverError(
                f"par.faultgeom entry {g!r} has {len(g)} fields; expected "
                "5 (EQquasi) or 6 (EQdyna)")
    return boxes


def expected_grid(par):
    """Per-fault (nfx, nfz), and the (nfxMax, nfzMax, ntotft) the padded
    handover array must have -- same formula as both codes' own
    netcdf_write_on_fault / netcdf_read_on_fault_eqdyna_restart."""
    dx = par.dx
    ntotft = getattr(par, "ntotft", 1)
    boxes = fault_boxes(par)
    if len(boxes) != ntotft:
        raise HandoverError(
            f"par.ntotft = {ntotft} but {len(boxes)} fault box(es) derived "
            "from par.faultgeom/fxmin-fxmax -- the problem definition is "
            "internally inconsistent, fix the compset before trusting any "
            "handover check against it")
    per_fault = []
    for ift, (xlo, xhi, zlo, zhi) in enumerate(boxes, start=1):
        nfx = round((xhi - xlo) / dx) + 1
        nfz = round((zhi - zlo) / dx) + 1
        per_fault.append((nfx, nfz))
    nfx_max = max(n for n, _ in per_fault)
    nfz_max = max(n for _, n in per_fault)
    return per_fault, nfx_max, nfz_max, ntotft


def open_file(path):
    try:
        import netCDF4 as nc
    except ImportError:
        raise HandoverError(
            "python netCDF4 module is not importable in this environment; "
            "install it (it is required to check any handover file) rather "
            "than skip the check")
    if not os.path.exists(path):
        raise HandoverError(f"handover file does not exist: {path}")
    return nc.Dataset(path, "r")


def check_required_vars(ds, path):
    missing = [v for v in REQUIRED_VARS if v not in ds.variables]
    if missing:
        raise HandoverError(
            f"{path}: missing required on-fault variable(s) "
            f"{missing} -- the receiving code's restart reader "
            f"(netcdf_read_on_fault_restart / "
            f"netcdf_read_on_fault_eqdyna_restart) requires all of "
            f"{sorted(REQUIRED_VARS)}")


def check_units(ds, path):
    for var, unit in REQUIRED_VARS.items():
        v = ds.variables[var]
        actual = getattr(v, "units", None)
        if actual != unit:
            raise HandoverError(
                f"{path}: variable '{var}' has units {actual!r}, expected "
                f"{unit!r} (both codes' netcdf_io.f90 write/read this "
                f"variable in {unit!r}) -- a unit/sign-convention mismatch "
                f"between the writer and reader")


def check_shape(ds, path, par):
    per_fault, nfx_max, nfz_max, ntotft = expected_grid(par)
    for var in REQUIRED_VARS:
        shape = ds.variables[var].shape
        if len(shape) == 3:
            file_ntotft, file_nfz, file_nfx = shape
        elif len(shape) == 2:
            file_ntotft, (file_nfz, file_nfx) = 1, shape
        else:
            raise HandoverError(
                f"{path}: variable '{var}' has rank {len(shape)} "
                f"(shape {shape}); expected rank 2 (dip,strike) or 3 "
                f"(nid_fault,dip,strike)")
        if file_ntotft != ntotft:
            raise HandoverError(
                f"{path}: variable '{var}' carries {file_ntotft} fault(s) "
                f"but the receiving case's par.ntotft = {ntotft} -- "
                f"regenerate this handover file for the right case geometry")
        if (file_nfz, file_nfx) != (nfz_max, nfx_max):
            raise HandoverError(
                f"{path}: variable '{var}' has (dip,strike) = "
                f"({file_nfz},{file_nfx}), expected ({nfz_max},{nfx_max}) "
                f"from the receiving code's own fault grid "
                f"(par.dx={par.dx}, per-fault (nfx,nfz)={per_fault})")
    return per_fault, nfx_max, nfz_max, ntotft


def real_node_mask(nfz_max, nfx_max, ntotft, per_fault):
    """One (ntotft, nfz_max, nfx_max) boolean mask per fault: True for a
    real node (within that fault's own (nfx,nfz) box, top-left corner, per
    both codes' own padding convention), False for zero-padding."""
    mask = np.zeros((ntotft, nfz_max, nfx_max), dtype=bool)
    for k, (nfx, nfz) in enumerate(per_fault):
        mask[k, :nfz, :nfx] = True
    return mask


def as_3d(ds, var, ntotft):
    arr = np.asarray(ds.variables[var][:], dtype=np.float64)
    if arr.ndim == 2:
        arr = arr[np.newaxis, :, :]
    return arr


def check_finite(ds, path, mask, ntotft):
    for var in REQUIRED_VARS:
        arr = as_3d(ds, var, ntotft)
        bad = ~np.isfinite(arr) & mask
        if bad.any():
            ift, j, i = np.argwhere(bad)[0]
            raise HandoverError(
                f"{path}: variable '{var}' is non-finite "
                f"(value={arr[ift, j, i]!r}) at fault {ift + 1}, "
                f"node (strike={i + 1}, dip={j + 1}) -- a real (non-padding) "
                f"fault node")


def check_normal_stress(ds, path, mask, ntotft):
    arr = as_3d(ds, "effective_normal", ntotft)
    bad = (arr >= 0.0) & mask
    if bad.any():
        ift, j, i = np.argwhere(bad)[0]
        raise HandoverError(
            f"{path}: effective_normal = {arr[ift, j, i]!r} Pa >= 0 at "
            f"fault {ift + 1}, node (strike={i + 1}, dip={j + 1}) -- "
            f"effective normal stress must be negative (compressive) on "
            f"every real fault node; this project's sign convention is "
            f"compression-negative (e.g. bp1001's sigma_n = -25 MPa)")


def check_slip_rate_sign(ds, path, mask, ntotft):
    arr = as_3d(ds, "slip_rate", ntotft)
    bad = (arr < 0.0) & mask
    if bad.any():
        ift, j, i = np.argwhere(bad)[0]
        raise HandoverError(
            f"{path}: slip_rate = {arr[ift, j, i]!r} m/s < 0 at fault "
            f"{ift + 1}, node (strike={i + 1}, dip={j + 1}) -- slip_rate "
            f"is a magnitude (m/s) in both codes' convention and must be "
            f">= 0")


def check_velocity_convention(ds, path, mask, ntotft, direction):
    """EQdyna writes absolute particle velocities (vm, vs independent,
    typically vm ~= vs on a locked/creeping node); EQquasi currently writes
    antisymmetric relative half slip rates (vm ~= -vs). Detect which by the
    median relative residual |vm+vs| / max(|vm|,|vs|) over real, slipping
    nodes -- ~0 for the antisymmetric (buggy) convention, ~2 for the
    absolute (correct) one. See ANTISYM_MEDIAN_THRESHOLD's docstring for the
    measured values this threshold sits between."""
    sr = as_3d(ds, "slip_rate", ntotft)
    slipping = mask & (sr > 1e-12)
    use_mask = slipping if slipping.any() else mask
    for vm_name, vs_name in VELOCITY_PAIRS:
        vm = as_3d(ds, vm_name, ntotft)
        vs = as_3d(ds, vs_name, ntotft)
        denom = np.maximum(np.abs(vm), np.abs(vs))
        denom = np.where(denom < 1e-12, 1.0, denom)
        rel = np.abs(vm + vs) / denom
        sample = rel[use_mask]
        if sample.size == 0:
            continue
        med = float(np.median(sample))
        if med < ANTISYM_MEDIAN_THRESHOLD:
            # Most-antisymmetric real node, for the error message.
            rel_full = np.where(use_mask, rel, np.inf)
            ift, j, i = np.argwhere(rel_full == rel_full.min())[0]
            raise HandoverError(
                f"{path}: '{vm_name}'/'{vs_name}' are antisymmetric "
                f"(median relative residual {med:.4g} over real slipping "
                f"nodes; {vm_name}={vm[ift, j, i]!r}, "
                f"{vs_name}={vs[ift, j, i]!r} at fault {ift + 1}, node "
                f"(strike={i + 1}, dip={j + 1})), not absolute particle "
                f"velocities. {KNOWN_BUG_MSG}")


def check_fric_pc_l(par):
    """EQsimu's convert.py works around EQdyna hardwiring the normal-stress
    state-law length scale L to Dc by setting EQquasi's par.fric_pc_L =
    par.fric_rsf_Dc (PATHWAY_FORWARD.md P2 row, PR #22). Verify the fix
    actually landed in THIS generated file rather than assuming it."""
    if not hasattr(par, "fric_pc_L"):
        return  # this par has no fric_pc_L attribute (e.g. EQdyna's own).
    dc = getattr(par, "fric_rsf_Dc", None)
    if dc is None:
        raise HandoverError(
            "par.fric_pc_L is set but par.fric_rsf_Dc is not -- cannot "
            "verify the fric_pc_L=Dc workaround")
    if par.fric_pc_L != dc:
        raise HandoverError(
            f"par.fric_pc_L = {par.fric_pc_L!r} != par.fric_rsf_Dc = "
            f"{dc!r} -- EQsimu's convert.py fric_pc_L workaround "
            f"(PATHWAY_FORWARD.md P2 row) did not take effect in this "
            f"generated user_defined_params.py; EQdyna hardwires L=Dc, so "
            f"EQquasi must match it exactly or the two codes disagree on "
            f"the normal-stress state law")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--direction", required=True,
                     choices=["eqquasi_to_eqdyna", "eqdyna_to_eqquasi"])
    ap.add_argument("--file", required=True,
                     help="the handover .nc file about to be read")
    ap.add_argument("--params-dir", required=True,
                     help="the RECEIVING code's own case directory "
                          "(has its generated user_defined_params.py)")
    args = ap.parse_args(argv)

    path = os.path.abspath(args.file)
    params_dir = os.path.abspath(args.params_dir)
    par = load_receiver_par(params_dir)

    check_fric_pc_l(par)

    ds = open_file(path)
    try:
        check_required_vars(ds, path)
        per_fault, nfx_max, nfz_max, ntotft = check_shape(ds, path, par)
        check_units(ds, path)
        mask = real_node_mask(nfz_max, nfx_max, ntotft, per_fault)
        check_finite(ds, path, mask, ntotft)
        check_normal_stress(ds, path, mask, ntotft)
        check_slip_rate_sign(ds, path, mask, ntotft)
        check_velocity_convention(ds, path, mask, ntotft, args.direction)
    finally:
        ds.close()

    print(f"check_handover.py: OK: {path} ({args.direction}, "
          f"ntotft={ntotft}, {len(REQUIRED_VARS)} vars, all real nodes "
          f"finite, effective_normal<0, slip_rate>=0, absolute-velocity "
          f"convention)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

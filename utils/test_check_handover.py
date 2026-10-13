#! /usr/bin/env python3
"""
Standalone verification for utils/check_handover.py (this project has no
tests/ directory -- utils/convert.py's own "Checks before changing
convert.py" in CLAUDE.md is verified the same way, by directly running a
script, not by a pytest suite).

Builds a tiny synthetic 1-fault case (its own minimal user_defined_params.py,
independent of the pinned EQquasi/EQdyna checkouts) and three handover
files:
  good.nc     -- passes every check (absolute-velocity convention, sigma<0,
                 all finite)
  bad_sigma.nc -- one real node has effective_normal >= 0 (not compressive)
  bad_missing.nc -- missing the 'vzs' variable entirely
  bad_nan.nc  -- one real node has slip_rate = NaN

Run: python3 utils/test_check_handover.py
Exits 0 if check_handover.py passes good.nc and fails each bad_*.nc for the
right, named reason; exits 1 and prints which assertion failed otherwise.
"""
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

UTILS = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(UTILS, "check_handover.py")

NFX, NFZ = 5, 4   # a small fake fault grid: 5 along strike, 4 along dip
DX = 1000.0

PARAMS_PY = f'''"""Synthetic 1-fault case for test_check_handover.py. Not a real
EQsimu compset -- just enough attributes for check_handover.py's
expected_grid()/fault_boxes()."""
from types import SimpleNamespace

par = SimpleNamespace()
par.ntotft = 1
par.dx = {DX}
par.fxmin, par.fxmax = 0.0, {(NFX - 1) * DX}
par.fzmin, par.fzmax = 0.0, {(NFZ - 1) * DX}
par.fric_rsf_Dc = 0.14
par.fric_pc_L = par.fric_rsf_Dc
'''

REQUIRED_VARS = [
    "shear_strike", "shear_dip", "effective_normal", "slip_rate",
    "state_variable", "state_normal", "vxm", "vym", "vzm", "vxs", "vys", "vzs",
]
UNITS = {"shear_strike": "Pa", "shear_dip": "Pa", "effective_normal": "Pa",
         "slip_rate": "m/s", "state_variable": "unit", "state_normal": "Pa",
         "vxm": "m/s", "vym": "m/s", "vzm": "m/s",
         "vxs": "m/s", "vys": "m/s", "vzs": "m/s"}


def write_nc(path, corrupt=None):
    import netCDF4 as nc
    ds = nc.Dataset(path, "w", format="NETCDF4")
    ds.createDimension("dip", NFZ)
    ds.createDimension("strike", NFX)
    data = {}
    for v in REQUIRED_VARS:
        arr = np.zeros((NFZ, NFX), dtype=np.float64)
        if v == "effective_normal":
            arr[:] = -25.0e6   # compressive, as this project's compsets use
        elif v == "slip_rate":
            arr[:] = 1.0e-3
        elif v in ("vxm", "vxs", "vym", "vys", "vzm", "vzs"):
            # absolute particle velocity: vm == vs (not vm == -vs), and
            # nonzero so the antisymmetry residual isn't a 0/eps degenerate
            arr[:] = 2.0e-4
        data[v] = arr

    if corrupt == "sigma":
        data["effective_normal"][2, 3] = 1.0e6   # positive: not compressive
    elif corrupt == "nan":
        data["slip_rate"][1, 2] = float("nan")
    # "missing" is handled below by skipping a variable's creation entirely.

    for v in REQUIRED_VARS:
        if corrupt == "missing" and v == "vzs":
            continue
        var = ds.createVariable(v, np.float64, ("dip", "strike"))
        var.units = UNITS[v]
        var[:, :] = data[v]
    ds.close()


def run_checker(nc_path, params_dir):
    return subprocess.run(
        [sys.executable, CHECKER, "--direction", "eqdyna_to_eqquasi",
         "--file", nc_path, "--params-dir", params_dir],
        capture_output=True, text=True)


def main():
    tmp = tempfile.mkdtemp(prefix="check_handover_test_")
    try:
        with open(os.path.join(tmp, "user_defined_params.py"), "w") as f:
            f.write(PARAMS_PY)

        failures = []

        good = os.path.join(tmp, "good.nc")
        write_nc(good)
        r = run_checker(good, tmp)
        if r.returncode != 0:
            failures.append(f"good.nc: expected exit 0, got {r.returncode}\n"
                             f"{r.stdout}\n{r.stderr}")
        else:
            print("PASS: good.nc exits 0 ->", r.stdout.strip())

        cases = [
            ("bad_sigma", "sigma", ["effective_normal", "fault 1",
                                     "strike=4, dip=3"]),
            ("bad_missing", "missing", ["vzs", "missing"]),
            ("bad_nan", "nan", ["slip_rate", "non-finite", "fault 1",
                                 "strike=3, dip=2"]),
        ]
        for name, corrupt, must_name in cases:
            path = os.path.join(tmp, name + ".nc")
            write_nc(path, corrupt=corrupt)
            r = run_checker(path, tmp)
            if r.returncode == 0:
                failures.append(f"{name}.nc: expected nonzero exit, got 0\n"
                                 f"{r.stdout}")
                continue
            missing_tokens = [t for t in must_name if t not in r.stderr]
            if missing_tokens:
                failures.append(
                    f"{name}.nc: exit {r.returncode} (good, nonzero) but "
                    f"stderr is missing expected token(s) {missing_tokens}:"
                    f"\n{r.stderr}")
            else:
                print(f"PASS: {name}.nc exits {r.returncode}, "
                      f"names {must_name} ->")
                print("   " + r.stderr.strip().replace("\n", "\n   "))

        if failures:
            print("\nFAILURES:")
            for f in failures:
                print(" -", f)
            return 1
        print("\nAll test_check_handover.py checks passed.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

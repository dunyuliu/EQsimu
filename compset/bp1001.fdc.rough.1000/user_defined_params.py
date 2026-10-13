"""
SEAS BP1001 at a 1 km on-fault grid: the same problem as
bp1001.fdc.rough.250 (loaded from there, Rule 7 -- a problem is defined
once), overriding only what the coarser grid changes:
  par.dx
  par.roughness -- kind="resample": the 1 km heights are never pre-baked
                   into a file here; roughness.heights() derives them from
                   the 250 m compset's rough_heights.250.txt at
                   problem-conversion time (low-pass to a 2 km cutoff,
                   decimate 4:1; utils/roughness.resample)
  par.eqdyna["casename"]
  par.eqdyna["nuni_y_plus"]/["nuni_y_minus"] -- re-derived to the same
                   physical far-boundary buffer (ceil(70*250/par.dx) cells)
See README.md.
"""
import importlib.util
import math
import os

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "eqsimu_bp1001_fdc_rough_250",
    os.path.join(_here, "..", "bp1001.fdc.rough.250", "user_defined_params.py"))
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

par = _base.par

par.dx = 1000.0e0
par.roughness = dict(kind="resample",
                     path="../bp1001.fdc.rough.250/rough_heights.250.txt",
                     from_dx=250.0, cutoff=2000.0)

par.eqdyna = dict(par.eqdyna)
par.eqdyna["casename"] = "bp1001.fdc.rough.1000.dyna"
par.eqdyna["nuni_y_plus"] = par.eqdyna["nuni_y_minus"] = \
    math.ceil(70*250/par.dx)
# dt = 0.25*dx/vp was computed from the 250 m compset's par.dx above;
# recompute for this dx (it is a formula in par.dx, not a fixed number).
par.eqdyna["dt"] = 0.25*par.dx/par.vp

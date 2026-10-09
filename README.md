# EQsimu

Earthquake cycle simulations with EQquasi (quasi-static, interseismic) and
EQdyna (dynamic rupture), coupled into fully dynamic cycles. Associated with
Liu et al. (2020).

EQsimu holds no solver code. It defines each **problem** once, in
`compset/<name>/user_defined_params.py`, and converts it into the
`user_defined_params.py` that EQquasi and EQdyna each read
(`utils/convert.py`). Fault roughness is built the same way: one surface on
the problem's fault grid, written as the `bFault_Rough_Geometry.txt` both
codes read (`utils/roughness.py`). Each code then runs its own workflow.

## Install

```
./checkout.sh -i ls6        # clone EQquasi + EQdyna at the commits in components.txt, build
source checkout.sh          # set EQSIMUROOT, EQQUASIROOT, EQDYNAROOT, PATH
```
`./checkout.sh -u ls6` moves existing checkouts to the pinned commits and
rebuilds. To move a pin, edit `components.txt`.

## Run a case

```
create.newcase MODE CASE COMPSET
```
| MODE | Code | |
|---|---|---|
| `qdc` | EQquasi | quasi-dynamic cycle |
| `dr`  | EQdyna | dynamic rupture |
| `fdc` | EQquasi + EQdyna | fully dynamic cycle; then `./case.setup && ./case.submit` in CASE |

Each case keeps `eqsimu/` with the problem, the generated files, and the commit
of EQsimu and of each code.

An fdc case runs, per cycle, one EQquasi job and then one EQdyna job, each
through that code's own `run.sh`. EQsimu passes only the restart files
(`fault.r.nc` to EQdyna, `fault.dyna.r.nc` back to EQquasi). Results land in
`eqquasi/result/cycle<k>/` and `eqdyna/result/cycle<k>/`. The cycles run are
`istart`–`iend` in the case's `user_defined_params.py`.

## Problems

| Compset | |
|---|---|
| [`bp1001.fdc.rough.250`](compset/bp1001.fdc.rough.250/README.md) | SEAS BP1001, rough fault, 250 m |

A new problem is a folder in `compset/` with a `user_defined_params.py`
(`par = problem()`, see `utils/problemDefaults.py`), its input files, and a
README with `setup.png` from `utils/plot_problem.py`. Roughness is
`par.roughness`: `dict(kind="file", path=...)` for a heights file in the
folder, `dict(kind="fractal", hurst=1.0, alpha=0.005, seed=1)` for EQdyna's
synthetic self-similar surface, or `None` for a planar fault.

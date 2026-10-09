# CLAUDE.md

EQsimu defines earthquake-cycle problems once and runs them with EQquasi and
EQdyna. It owns no solver code (`PROJECT_RULES.md`).

- `compset/<name>/user_defined_params.py`: the problem (`par = problem()`,
  `utils/problemDefaults.py`)
- `utils/convert.py`: the API, problem to each code's `user_defined_params.py`
- `utils/roughness.py`: the problem's fault surface, written as the
  `bFault_Rough_Geometry.txt` both codes read
- `utils/create.newcase`: convert, then stage with each code's `create.newcase`
- `utils/case.setup`: the fdc chain, per cycle EQquasi then EQdyna, each via
  its own `run.sh`; EQsimu hands over only `fault.r.nc` / `fault.dyna.r.nc`
- `components.txt`: pinned EQquasi / EQdyna commits; `checkout.sh` uses them

## Commands

```
./checkout.sh -i ls6 | -u ls6       # install / move to pins (bash)
source checkout.sh                  # env only
create.newcase fdc CASE COMPSET     # or qdc / dr
python3 utils/plot_problem.py compset/<name>    # setup.png for the README
```
Work in raw bash, not conda.

## Checks before changing convert.py

- The EQquasi output must match that code's own compset `par` exactly
  (bp1001: all attributes and `on_fault_vars` equal; `xcoor` is a loop leftover).
- `create.newcase fdc` then `./case.setup` must run with the pinned codes.
- `roughness.fractal_surface` must equal EQdyna's
  `generateFaultInterface:generateFractalSurface` bitwise for the same seed.

## Conventions

- No personal names in docs, commits, or the board; name codes (EQquasi,
  EQdyna). Citations (Author Year) and LICENSE lines stay.
- Open gaps live in `PATHWAY_FORWARD.md`.

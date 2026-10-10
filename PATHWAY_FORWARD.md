# Pathway Forward

## Owner decisions (verbatim)

- 2026-10-09, uncommitted-redesign question ("Can the autopilot conductor
  commit the uncommitted redesign?"): **"Commit to a branch (Recommended)"**
  — "Commit the redesign to a feature branch and push it to origin. The
  conductor then works the board through gated PRs against that branch."
  This lifted the prior "leave all changes uncommitted" instruction.
- 2026-10-09, on the 1 km bp1001 variant: **"just be careful, resample
  shouldn't simply pick py/px from the 250 grids."**
- 2026-10-09, on the 1 km roughness: **"it has to go through the script to
  recompute dy/dx."**
- 2026-10-09, on how the 1 km heights come from the 250 m file (asked:
  low-pass at 2 km before sampling, rather than taking every 4th point;
  dy/dx and dy/dz then recomputed by `roughness.py` at 1 km):
  **"sounds good"**.

| Priority | Item | Command | Last checked |
|---|---|---|---|
| P1 | fdc never run for real with the pinned codes; the chain is tested only with stub `sbatch`/`mpirun`. BLOCKED(owner): ls6 needs an MFA session ("Later"); locally, the choice is between the existing builds in the `eqquasi-petsc` conda env (EQquasi at the pin, EQdyna at `447fc4a`, needs a rebuild at the pin) and a fresh `checkout.sh -i` | `create.newcase fdc t bp1001.fdc.rough.1000 --machine local && cd t && ./case.setup && ./case.submit` | 2026-10-10 |
| P2 | Stepover fdc: the restart files do not match for `ntotft>1`. EQquasi's `fault.r.nc` holds all faults in one 3-D file; EQdyna mode 2 reads tagged per-fault variables that no code writes, and writes fault 2 to `fault.dyna.r_ft2.nc`. Conversion works (`compset/test.stepover.2fault`, qdc only). BLOCKED(owner): proposed fix is upstream in EQdyna, matching EQquasi's file | `create.newcase fdc t test.stepover.2fault` with `par.mode = 2`, then confirm EQdyna reads the `fault.r.nc` it is handed | 2026-10-10 |
| P2 | Pins in `components.txt` are the 2026-10-09 heads, not the versions behind Liu et al. (2020) | `git -C components/eqquasi log --until=2020-12-31 -1` | 2026-10-09 |
| P3 | The 1 km low-pass (`roughness.resample`, Gaussian, 2 km cutoff) still passes about 37% amplitude at 2 km, the Nyquist wavelength of the 1 km grid; sharpen only if the owner asks | `grep -n "def resample" -A30 utils/roughness.py` | 2026-10-10 |
| P3 | EQdyna's own `case_input/bp1001.fdc.rough.250` is in the flat pre-`par` format its `case.setup` no longer imports; report to EQdyna | `grep -c 'par = parameters' components/eqdyna/case_input/bp1001.fdc.rough.250/user_defined_params.py` | 2026-10-09 |
| P3 | The liu2020 cases (`liu2020.fdc.planar`, `liu2020.fdc.rough.250` in both codes) are not yet EQsimu compsets | `ls compset` | 2026-10-10 |
| P3 | `utils/case.setup` rewrites two lines of EQquasi's `run.sh` (cycle loop, restart source) into `run.cycle.sh`, and stops if either line changes upstream | `create.newcase fdc t bp1001.fdc.rough.250 && cd t && ./case.setup` | 2026-10-09 |

Closed rows are in git history (`git log -p PATHWAY_FORWARD.md`).

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
- 2026-10-10, on the local-run choice (asked: the existing builds in the
  `eqquasi-petsc` conda env, or a fresh `checkout.sh -i`): **"Use existing
  env for now"**.

| Priority | Item | Command | Last checked |
|---|---|---|---|
| P1 | fdc on ls6 never run; locally `bp1001.fdc.rough.1000` ran two cycles for real on 2026-10-10/11 (`eqquasi-petsc` env, EQquasi `eqquasi-1.21.2` = pin source, EQdyna built at the pin): each EQquasi phase ended by handing over to EQdyna, and cycle 2's EQquasi started at peak slip rate 7.814489e-3 m/s, equal to the maximum in cycle 1's `fault.dyna.r.nc`. BLOCKED(owner): ls6 needs an MFA session ("Later") | `create.newcase fdc t bp1001.fdc.rough.1000 --machine ls6 && cd t && ./case.setup && ./case.submit` | 2026-10-11 |
| P2 | `test.stepover.2fault` never run as a real fdc case; its two-fault restart hand-off is tested only as an I/O round trip in EQdyna's own tests | `create.newcase fdc t test.stepover.2fault --machine local && cd t && ./case.setup && ./case.submit` | 2026-10-11 |
| P3 | At 1 km, EQdyna drops the 7 on-fault stations at 7.5 km depth (not a node of the 1 km grid; it warns, no `faultst*` file); keep the 250 m station set, or move them for this compset — owner's call | `grep -A9 'WARNING: 7 of 13' <case>/eqdyna/result/cycle0/*.log` | 2026-10-11 |
| P2 | Pins in `components.txt` are recent heads (EQquasi 2026-10-09, EQdyna `42ce254` 2026-10-10), not the versions behind Liu et al. (2020) | `git -C components/eqquasi log --until=2020-12-31 -1` | 2026-10-09 |
| P3 | The 1 km low-pass (`roughness.resample`, Gaussian, 2 km cutoff) still passes about 37% amplitude at 2 km, the Nyquist wavelength of the 1 km grid; sharpen only if the owner asks | `grep -n "def resample" -A30 utils/roughness.py` | 2026-10-10 |
| P3 | EQdyna's own `case_input/bp1001.fdc.rough.250` is in the flat pre-`par` format its `case.setup` no longer imports; report to EQdyna | `grep -c 'par = parameters' components/eqdyna/case_input/bp1001.fdc.rough.250/user_defined_params.py` | 2026-10-09 |
| P3 | The liu2020 cases (`liu2020.fdc.planar`, `liu2020.fdc.rough.250` in both codes) are not yet EQsimu compsets | `ls compset` | 2026-10-10 |
| P3 | `utils/case.setup` rewrites two lines of EQquasi's `run.sh` (cycle loop, restart source) into `run.cycle.sh`, and stops if either line changes upstream | `create.newcase fdc t bp1001.fdc.rough.250 && cd t && ./case.setup` | 2026-10-09 |

Closed rows are in git history (`git log -p PATHWAY_FORWARD.md`).

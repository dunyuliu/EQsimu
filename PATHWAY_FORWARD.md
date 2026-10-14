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
- 2026-10-11, on (1) the 1 km stations at 7.5 km depth (keep the 250 m set,
  note the gap in the 1 km README) and (2) running `test.stepover.2fault` as
  a real fdc case: **"Go"**.
- 2026-10-12, on adding the local conda-env exception to `CLAUDE.md`
  (asked: add a one-line carve-out, or leave it board-only): **"1 yes"**.
- 2026-10-12, on the `test.stepover.2fault` cycle-2 restart failure:
  **"both codes should handle the stresses and other physical vars in same
  fashion."** and **"can you nail down which one has ptential issues?"**
- 2026-10-12, on the normal-stress state law differing between the codes
  (EQdyna: L = Dc; EQquasi: `fric_pc_L`, default 0):
  **"they should use same input, same model setup on the fault"**, and
  **"i don't expect issues to connect"**.
- 2026-10-12, on mismatches between the codes and on the handover files:
  **"if the mismatch is upstream, report. eqsimu should have checks on
  transfer files and if any inconsistency, break"**.
- 2026-10-12, on the velocity convention in the restart files (asked: break,
  warn, or investigate first): **"Particle vel should be right."**; on adding
  the `fric_pc_L` exception to `CLAUDE.md`'s parity check: **"Yes, add it
  (Recommended)"**, then **"But should keep in board that this needs fix"**.
- 2026-10-13, on non-compressive effective normal stress (asked: clamp to 0
  in both codes, stop in both, or a shared input): **"Clamp to 0 in both
  (Recommended)"**.
- 2026-10-13, on the normal-stress caps mismatch (`test.stepover.2fault`
  turns EQquasi's caps on, while EQdyna caps only when `insertFaultType>0`
  and `C_elastic==1`, so not on this planar case; asked: a) caps off in the
  compset, b) keep caps on and report to EQdyna, c) both): **"2b"**.
- 2026-10-13, on the pins (current `components.txt` heads, EQquasi
  `524a5236` / EQdyna `42ce254`, or the commits nearest the 2020 paper,
  EQquasi `66958e3` / EQdyna `0381248`): **"current. let's reproduce
  later"**.
- 2026-10-13, on the restart velocities, after reading how each code
  builds them (EQdyna integrates each side's momentum; EQquasi, quasi-static,
  splits the slip rate by mass): **"eqquasi moment is 0."**, **"so particle
  vel depends on mass"**, **"and they split the slip"**, then **"go"** and
  **"update the check"**. Read as: EQquasi's velocities are valid; the
  handover check compares only |v_m − v_s| with slip_rate (option 1d), and
  "go" also takes 4b (ask EQdyna to stop at sigma_bar >= 0, as EQquasi does).
- 2026-10-13, on PRs and releases (after the redesign sat on a side branch
  with a draft PR and no release): **"I mean pr should be going to EQsimu
  and get updated quicker"**, **"Releases more often"**, **"A branch stayed
  finite"**. Read as: PRs to `main`, short-lived branches, a release per
  landed surface.

| Priority | Item | Command | Last checked |
|---|---|---|---|
| P1 | Non-compressive effective normal stress (sigma_bar >= 0): EQquasi stops on purpose (`check_effective_normal`, `STOP 508`; its old clamp-to-zero gave NaN from the Newton solve), EQdyna clamps to 0 silently on every geometry (`src/fortran/faulting.f90:224-225` at the pin). The owner's 2026-10-13 "clamp to 0 in both" would undo EQquasi's fix, so it was taken as asking EQdyna to stop like EQquasi: https://github.com/EQDYNA/EQdyna/issues/201. Related caps report: https://github.com/EQDYNA/EQdyna/issues/200. Not fixable in `convert.py` (no input in either code) | `gh issue view 201 -R EQDYNA/EQdyna --json state` | 2026-10-13 |
| P1 | fdc on ls6 never run; locally `bp1001.fdc.rough.1000` ran two cycles for real (rerun 2026-10-13 with `fric_pc_L = Dc`) (`eqquasi-petsc` env, EQquasi `eqquasi-1.21.2` = pin source, EQdyna built at the pin): each EQquasi phase ended by handing over to EQdyna, and cycle 2's EQquasi started at peak slip rate 4.65613e-3 m/s, equal to the maximum in cycle 1's `fault.dyna.r.nc`. BLOCKED(owner): ls6 needs an MFA session ("Later") | `create.newcase fdc t bp1001.fdc.rough.1000 --machine ls6 && cd t && ./case.setup && ./case.submit` | 2026-10-13 |
| P2 | Normal-stress state-law length L: EQdyna hardwires L = Dc per node, EQquasi takes `fric_pc_L` (default 0), so EQquasi lost the lag EQdyna handed over and `test.stepover.2fault` cycle 2 stopped with `STOP 508`. EQsimu works around it (`utils/convert.py` sets EQquasi's `fric_pc_L = Dc`, PR #22; cycle 2 now runs). Needs the upstream fix: EQdyna to take L as an input, https://github.com/EQDYNA/EQdyna/issues/189; then both codes get it from the problem | `gh issue view 189 -R EQDYNA/EQdyna --json state` | 2026-10-12 |
| P2 | Pins in `components.txt` are recent heads (EQquasi 2026-10-09, EQdyna `42ce254` 2026-10-10), not the versions behind Liu et al. (2020): EQquasi's nearest-to-2020-12-31 commit is `66958e3` (2020-10-08), EQdyna's is `0381248` (2020-10-07) | `git -C components/eqquasi log --until=2020-12-31 -1` | 2026-10-12 |
| P3 | The 1 km low-pass (`roughness.resample`, Gaussian, 2 km cutoff) still passes about 37% amplitude at 2 km, the Nyquist wavelength of the 1 km grid; sharpen only if the owner asks | `grep -n "def resample" -A30 utils/roughness.py` | 2026-10-10 |
| P3 | EQdyna's own `case_input/bp1001.fdc.rough.250` is in the flat pre-`par` format its `case.setup` no longer imports (0 matches for `par = parameters` in the pinned `42ce254` copy); report to EQdyna | `grep -c 'par = parameters' components/eqdyna/case_input/bp1001.fdc.rough.250/user_defined_params.py` | 2026-10-12 |
| P3 | The liu2020 cases (`liu2020.fdc.planar`, `liu2020.fdc.rough.250` in both codes) are not yet EQsimu compsets | `ls compset` | 2026-10-10 |
| P3 | `utils/case.setup` rewrites two lines of EQquasi's `run.sh` (cycle loop, restart source) into `run.cycle.sh`, and stops if either line changes upstream | `create.newcase fdc t bp1001.fdc.rough.250 && cd t && ./case.setup` | 2026-10-09 |

Closed rows are in git history (`git log -p PATHWAY_FORWARD.md`).

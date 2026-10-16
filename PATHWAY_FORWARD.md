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
- 2026-10-15, on moving the EQdyna pin past `42ce254` (asked: move it to
  `46ee862`, which fixed EQdyna #189/#200/#201, via a `components.txt` bump,
  rule-8 check, `convert.py` passing the same `fric_pc_L` and caps to both
  codes, board update and release): **"upstream updated and you can move
  forward?"**, then **"/autopilot march on"**. Read as: go, to the current
  EQdyna head. Landed: pin -> `29774c3` (head at bump time; commits
  `46ee862`..`29774c3` are board/docs/testsys only, EQdyna PRs #213-#216),
  `C_normal_stress_caps` moved into `utils/convert.py`'s shared `COMMON` so
  both codes get the same value (was EQquasi-only), rule 8 green for all 3
  compsets x both codes. `fric_pc_L` was already effectively shared (see P2
  row); no further convert.py change needed there.
- 2026-10-15, on the stepover fdc (asked: (1) rerun `test.stepover.2fault`
  locally past the cycle-2 handover once the EQdyna pin moves, the 2026-10-12
  run having stopped mid cycle-2 EQquasi with the case since deleted; (4) the
  handover check not yet run on a stepover): **"1 go"**.

| Priority | Item | Command | Last checked |
|---|---|---|---|
Closed 2026-10-15: non-compressive effective normal stress and the caps input
(prior P1/P2 rows). EQdyna pin moved past `42ce254` to `29774c3` (PR #210,
`46ee862`+): EQdyna now stops on `sigma_bar >= 0`
(`stopNonCompressiveNormal`, `src/fortran/faulting.f90:247`), like EQquasi's
`check_effective_normal`/`STOP 508`. `C_normal_stress_caps` is now shared
(`utils/convert.py`'s `COMMON`, was EQquasi-only); rule 8 confirms both codes
read `C_normal_stress_caps = 1` for every compset
(`bash rule8.sh <eqquasiroot> <eqdynaroot> <out>`).
| P1 | fdc on ls6 never run; locally `bp1001.fdc.rough.1000` ran two cycles for real (rerun 2026-10-13 with `fric_pc_L = Dc`) (`eqquasi-petsc` env, EQquasi `eqquasi-1.21.2` = pin source, EQdyna built at the pin): each EQquasi phase ended by handing over to EQdyna, and cycle 2's EQquasi started at peak slip rate 4.65613e-3 m/s, equal to the maximum in cycle 1's `fault.dyna.r.nc`. BLOCKED(owner): ls6 needs an MFA session ("Later") | `create.newcase fdc t bp1001.fdc.rough.1000 --machine ls6 && cd t && ./case.setup && ./case.submit` | 2026-10-13 |
| P2 | Normal-stress state-law length L: EQsimu's `utils/convert.py` still sets EQquasi's `fric_pc_L = Dc` explicitly (PR #22 workaround; EQquasi's own default, 0.0, means "no state," unlike EQdyna's). EQdyna pin `29774c3` now takes `par.fric_pc_L` too (`None` default = per-node Dc, same value as EQquasi's override, so the two codes already agree in effect; verified bitwise-equal L is not). rule 8 (2026-10-15) shows `eqquasi fric_pc_L=0.14` (=Dc) and `eqdyna fric_pc_L=None` for every compset, the same L by construction (`_check_uniform_dc`). Left open upstream: EQdyna's explicit theta_pc update vs EQquasi's exponential one | `bash rule8.sh <eqquasiroot> <eqdynaroot> <out>` | 2026-10-15 |
| P2 | Pins in `components.txt` are recent heads (EQquasi 2026-10-09, EQdyna `29774c3` 2026-10-15), not the versions behind Liu et al. (2020): EQquasi's nearest-to-2020-12-31 commit is `66958e3` (2020-10-08), EQdyna's is `0381248` (2020-10-07) | `git -C components/eqquasi log --until=2020-12-31 -1` | 2026-10-15 |
| P3 | The 1 km low-pass (`roughness.resample`, Gaussian, 2 km cutoff) still passes about 37% amplitude at 2 km, the Nyquist wavelength of the 1 km grid; sharpen only if the owner asks | `grep -n "def resample" -A30 utils/roughness.py` | 2026-10-10 |
| P3 | EQdyna's own `case_input/bp1001.fdc.rough.250` is in the flat pre-`par` format its `case.setup` no longer imports (0 matches for `par = parameters` in the pinned `42ce254` copy); report to EQdyna | `grep -c 'par = parameters' components/eqdyna/case_input/bp1001.fdc.rough.250/user_defined_params.py` | 2026-10-12 |
| P3 | The liu2020 cases (`liu2020.fdc.planar`, `liu2020.fdc.rough.250` in both codes) are not yet EQsimu compsets | `ls compset` | 2026-10-10 |
| P3 | `utils/case.setup` rewrites two lines of EQquasi's `run.sh` (cycle loop, restart source) into `run.cycle.sh`, and stops if either line changes upstream | `create.newcase fdc t bp1001.fdc.rough.250 && cd t && ./case.setup` | 2026-10-09 |

Closed rows are in git history (`git log -p PATHWAY_FORWARD.md`).

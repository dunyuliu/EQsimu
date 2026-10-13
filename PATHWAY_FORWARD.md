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

| Priority | Item | Command | Last checked |
|---|---|---|---|
| P1 | On-fault input audit, positive effective-normal-stress (sigma_bar >= 0) handling: UPSTREAM MISMATCH, confirmed against the `components.txt` pins (EQquasi `524a5236b411c38fa216cff97bc6949bd83721e1`, EQdyna `42ce254085abad7a85c803b0b8dc1a7c33c5a261`, resolved via `git show <pin>:<path>`, not the ambient checkout — see Rule 9), not fixable in EQsimu's `convert.py` since both behaviors are hardwired in each code's Fortran with no exposed parameter. EQquasi (`src/faulting.f90`, subroutine `check_effective_normal`): `if (tnrm0 < 0.0d0) return`, else writes a diagnostic and `STOP 508` when sigma_bar >= 0. EQdyna (`src/fortran/faulting.f90:224-225`): unconditional `if (nsdTractionVector(1) > 0.0d0) nsdTractionVector(1) = 0.0d0` — that clamp sits after the nearby `if (insertFaultType>0 .and. C_elastic==1)` block's own `endif` at line 221, so it fires on every fault geometry (planar included), not only rough+elastic faults. One code crashes, the other silently masks an invalid physical state (rate-and-state has no solution at sigma_bar >= 0). The same audit's v0/f0 (reference slip rate / friction coefficient) and loading-slip-rate sub-items CLOSED 2026-10-12: both codes read these from matching on-fault array slots and `convert.py`'s COMMON mechanism passes identical values (bp1001: `fric_rsf_v0`=1e-6 m/s, `fric_rsf_r0`=0.6, `creep_slip_rate`=1e-9 m/s); no `convert.py` change needed. Needs an upstream report to EQdyna; the report text is the conductor's to draft and send to the owner before filing, not this row's | `git show 42ce254085abad7a85c803b0b8dc1a7c33c5a261:src/fortran/faulting.f90 \| sed -n '210,230p'` (EQdyna pin); `git show 524a5236b411c38fa216cff97bc6949bd83721e1:src/faulting.f90 \| grep -n check_effective_normal` (EQquasi pin) | 2026-10-12 |
| P1 | fdc on ls6 never run; locally `bp1001.fdc.rough.1000` ran two cycles for real on 2026-10-10/11 (`eqquasi-petsc` env, EQquasi `eqquasi-1.21.2` = pin source, EQdyna built at the pin): each EQquasi phase ended by handing over to EQdyna, and cycle 2's EQquasi started at peak slip rate 7.814489e-3 m/s, equal to the maximum in cycle 1's `fault.dyna.r.nc`. BLOCKED(owner): ls6 needs an MFA session ("Later") | `create.newcase fdc t bp1001.fdc.rough.1000 --machine ls6 && cd t && ./case.setup && ./case.submit` | 2026-10-11 |
| P2 | Normal-stress state-law length L: EQdyna hardwires L = Dc per node, EQquasi takes `fric_pc_L` (default 0), so EQquasi lost the lag EQdyna handed over and `test.stepover.2fault` cycle 2 stopped with `STOP 508`. EQsimu works around it (`utils/convert.py` sets EQquasi's `fric_pc_L = Dc`, PR #22; cycle 2 now runs). Needs the upstream fix: EQdyna to take L as an input, https://github.com/EQDYNA/EQdyna/issues/189; then both codes get it from the problem | `gh issue view 189 -R EQDYNA/EQdyna --json state` | 2026-10-12 |
| P2 | Restart velocities: EQquasi writes `vxm…vzs` as antisymmetric relative half slip rates, EQdyna as absolute particle velocities; owner: particle velocities are right. Needs an EQquasi fix (report upstream). EQsimu's transfer-file check landed (PR #25, `d5dc834`) and runs this check at every handover; verified working as intended: it passes on EQdyna's output in both directions and exits 1 on EQquasi's `fault.r.nc`, naming `vxm`/`vxs` as antisymmetric (median relative residual ~0 on real nodes), confirmed on real `test.stepover.2fault` and `bp1001.fdc.rough.1000` artifacts | `python3 utils/check_handover.py --direction eqquasi_to_eqdyna --file <eqquasi/result/cycleN/fault.r.nc> --params-dir <eqdyna-case-dir>` | 2026-10-12 |
| P1 | fdc chain now hard-fails every run, by design: `utils/check_handover.py` (PR #25) exits 1 on every real EQquasi-to-EQdyna handover (antisymmetric `vxm`/`vxs` vs. EQdyna's absolute convention, row above) and `case.setup` enforces it before EQdyna starts. This blocks `test.stepover.2fault`, `bp1001.fdc.rough.1000`, and `bp1001.fdc.rough.250` past their first EQquasi phase until EQquasi's velocity convention is fixed upstream; "fdc chain runs end to end" does not hold for any compset right now | `create.newcase fdc t bp1001.fdc.rough.1000 --machine ls6 && cd t && ./case.setup && ./case.submit` (fails at first EQquasi-to-EQdyna handover) | 2026-10-12 |
| P2 | Pins in `components.txt` are recent heads (EQquasi 2026-10-09, EQdyna `42ce254` 2026-10-10), not the versions behind Liu et al. (2020): EQquasi's nearest-to-2020-12-31 commit is `66958e3` (2020-10-08), EQdyna's is `0381248` (2020-10-07) | `git -C components/eqquasi log --until=2020-12-31 -1` | 2026-10-12 |
| P3 | The 1 km low-pass (`roughness.resample`, Gaussian, 2 km cutoff) still passes about 37% amplitude at 2 km, the Nyquist wavelength of the 1 km grid; sharpen only if the owner asks | `grep -n "def resample" -A30 utils/roughness.py` | 2026-10-10 |
| P3 | EQdyna's own `case_input/bp1001.fdc.rough.250` is in the flat pre-`par` format its `case.setup` no longer imports (0 matches for `par = parameters` in the pinned `42ce254` copy); report to EQdyna | `grep -c 'par = parameters' components/eqdyna/case_input/bp1001.fdc.rough.250/user_defined_params.py` | 2026-10-12 |
| P3 | The liu2020 cases (`liu2020.fdc.planar`, `liu2020.fdc.rough.250` in both codes) are not yet EQsimu compsets | `ls compset` | 2026-10-10 |
| P3 | `utils/case.setup` rewrites two lines of EQquasi's `run.sh` (cycle loop, restart source) into `run.cycle.sh`, and stops if either line changes upstream | `create.newcase fdc t bp1001.fdc.rough.250 && cd t && ./case.setup` | 2026-10-09 |

Closed rows are in git history (`git log -p PATHWAY_FORWARD.md`).

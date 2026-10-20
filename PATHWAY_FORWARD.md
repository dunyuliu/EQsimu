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
- 2026-10-15, same question, (2) the caps mismatch on the stepover (EQquasi
  caps on; EQdyna at `42ce254` capped only non-planar faults): **"2, you open
  it"**. Read as: caps on in both codes for the stepover; landed with the pin
  bump (PR #37, `C_normal_stress_caps = 1` shared).
- 2026-10-15, stepover-fdc-rerun attempt (mission "wei-lin" stepover rerun):
  the rerun at the current pins (EQquasi `524a5236`, EQdyna `29774c3`)
  BLOCKED in the build step, before any case existed -- `./checkout.sh -i
  local` (`eqquasi-petsc` conda env active) fails building EQquasi's
  private MUMPS: on this host, MUMPS's CMake `find_package(MPI)` picks the
  system OpenMPI 3.1 (`/usr/lib/x86_64-linux-gnu/openmpi`) over the conda
  env's, and errors `Could NOT find MPI (missing: MPI_Fortran_FOUND
  Fortran)`, so `mumps/build/local/include/dmumps_struc.h` never exists and
  EQquasi's own `make` then fails on `solveTimeLoopMUMPS.f90` with `Fatal
  Error: Cannot open included file 'dmumps_struc.h'`. A retry exporting
  `CC`/`FC`/`CXX`/`MPI_HOME`/`CMAKE_PREFIX_PATH` to the conda env's MPI
  wrappers before `install.mumps.sh`: got CMake's `find_package(MPI)` to
  pick the conda env (`Found MPI_C`/`Found MPI_Fortran` ->
  `$CONDA_PREFIX/bin/mpicc`/`mpif90`), but MUMPS's CMake then fails on
  `Could NOT find LAPACK (missing: LAPACK_LIBRARIES)`
  (`cmake/FindLAPACK.cmake:489`) -- a second, different build-environment
  failure -- so `dmumps_struc.h` still never exists and EQquasi's build
  still fails the same way. Not retried a third time. No handover files
  were produced, so `check_handover.py` and
  the normal-stress-caps evidence are still open (see the two rows below).
  See `compset/test.stepover.2fault/README.md`'s Results section for the
  full command/error transcript.
- 2026-10-15, second stepover-fdc-rerun attempt, same pins: fixed the build
  by calling EQquasi's own `install.eqquasi.sh -m conda-linux` directly
  (not `checkout.sh -i local`, which can't express a per-component mode) --
  built in 5 s from the activated `eqquasi-petsc` env, no private MUMPS.
  `EQDYNAROOT` pointed at a prebuilt EQdyna already at the pin. `create.newcase
  fdc ... --machine local` and `./case.setup` both succeeded (caps confirmed
  ON in `case.setup`'s own log). `./case.submit` then BLOCKED in cycle 0: a
  new, different failure -- EQquasi's netcdf reader errors `NetCDF: Invalid
  dimension ID or name` on `input/on_fault_vars_input.nc` and a rank
  SIGSEGVs, before any rupture or handover. Read as an HDF5/netCDF
  library-version mismatch between the `venv` Python (`netCDF4` 1.7.2) that
  `create.newcase` used to write the file and the `eqquasi-petsc` conda
  env's `netcdf-fortran` that EQquasi links against on this host -- the same
  kind of file ran clean for 24,000+ steps on 2026-10-12, so this is
  host/env-specific, not a re-opened EQsimu bug. Not chased further this
  attempt. Still open: cycle-1/cycle-2 handover files,
  `check_handover.py` on all three, and caps-application evidence from an
  actual run (vs. the static `case.setup` confirmation that caps are
  configured ON). See `compset/test.stepover.2fault/README.md` for the
  full transcript.
- 2026-10-16, re-diagnosis of the 2026-10-15 netCDF crash: the prior
  "HDF5/netCDF library-version mismatch" read was WRONG, refuted directly. A
  standalone Fortran reader (`nf90_open`/`nf90_inq_varid`/
  `nf90_inquire_variable`/`nf90_inquire_dimension`/`nf90_get_var`), built from
  the same activated `eqquasi-petsc` env against the actual
  `on_fault_vars_input.nc` that crashed EQquasi, reads it correctly both
  serially and under the identical 6-rank `mpirun --bind-to none --mca btl
  self,sm --mca pml ob1` launch -- dims (26,11,2) match expectations, no
  error. The real cause is a `-O3` miscompilation inside EQquasi's own
  `components/eqquasi/src/netcdf_io.f90:netcdf_read_on_fault`: a bisected
  "hybrid" rebuild (every other file at the production `-O3`, only
  `netcdf_io.o` recompiled at `-O0 -g -fbacktrace -fcheck=all` then
  hand-linked with `make`'s own link line, since `make clean`'s link rule
  deletes the `.o`s) runs the stepover case cleanly past the netCDF read and
  1000+ further time steps at full `np=6` speed; the stock all-`-O3` binary
  crashes with `NetCDF: Invalid dimension ID or name` + SIGSEGV at the same
  point every time. So the file, the venv writer, and the conda netCDF/HDF5
  stack are all fine; EQquasi's own `-O3` build of `netcdf_io.f90` is not.
  Per the 2026-10-12 owner decision ("if the mismatch is upstream, report"),
  this is BLOCKED(upstream: EQquasi), not an EQsimu or host-env bug -- EQsimu
  owns no solver code. Reproduction recipe for the upstream report: pin
  `524a5236`, `eqquasi-petsc` env, compile `netcdf_io.f90` at `-O3` vs `-O0
  -fcheck=all` with everything else held fixed, run `test.stepover.2fault`
  cycle 0 against `input/on_fault_vars_input.nc`. Root line inside
  `netcdf_read_on_fault` (383-462) not pinned further this session -- the
  source already flags implicit-interface character-length risk at the call
  site (`eqquasi.f90:185-191`) as a related but distinct, already-verified-safe
  pattern (the one caller there passes a length-50 actual to a length-50
  dummy). Still open: cycle-1/cycle-2 handover files, `check_handover.py` on
  all three, caps-application evidence from an actual run -- none reachable
  until EQquasi fixes or a debug/workaround binary is approved for a real
  multi-cycle run (not proposed; `-O0 -fcheck=all` measured at ~5.7 s/step,
  np=6, vs. ~1.8 s/step production -- a full cycle would take hours).
- 2026-10-16, on the EQquasi `-O3` `netcdf_read_on_fault` crash (asked: (1)
  file the EQquasi upstream report, after pinning the failing line and
  compiler versions; (2) run the stepover locally with only that file at
  `-O0`): **"1"**.
- 2026-10-18, on running `test.stepover.2fault` fdc with EQquasi built at
  `-O2` (a compile flag only, no source change) while EQquasi #65 is open:
  **"Then why not try your self? Get a EQquasi copy and change flag"**.
- 2026-10-19, on cycle 2 of `test.stepover.2fault` ending at EQquasi's
  hardcoded 30000-step fdc limit without a rupture (asked: is it physical;
  should the chain break): **"Should continue EQquasi"**, **"Until next rpt"**.
- 2026-10-19, on tagging v0.2.0 on main (20 commits since v0.1.1; no CI, so
  the gate is a stranger clone plus the create.newcase/case.setup checks):
  **"Tag v0.2.0 now (Recommended)"**.
- 2026-10-19, on EQquasi 1.21.3+ refusing EQdyna's restart for lacking a
  `dip_node_spacing` attribute (blocks the pin move): **"EQdyna stamps it
  (Recommended)"** -- an upstream EQdyna PR writes its dz there; EQquasi's
  check stays strict.
- 2026-10-20, on cutting a release for the pin move to EQquasi `71f373e` /
  EQdyna `15346fc` (PR #60): **"Tag v0.2.1 now (Recommended)"**.
- 2026-10-20, on whether EQsimu tags and releases without asking: **"All
  non-major auto"**. Read as: a patch or minor release is tagged and
  published once the release gate passes on the exact SHA (fresh clone under
  `env -i`: `create.newcase fdc` + `case.setup` on every fdc compset,
  `utils/test_check_handover.py`, rule 8); a major bump still asks.
- 2026-10-16, next workable row (`liu2020 compsets`, both P1s staying
  BLOCKED): landed `liu2020.fdc.planar.300` and `liu2020.fdc.rough.250` as
  EQsimu compsets (PR #49), reconciling EQdyna's and EQquasi's existing
  native `liu2020.fdc.planar`/`liu2020.fdc.rough.250` case_input into one
  canonical `problem()` each. `liu2020.fdc.rough.250`'s `par.init_norm =
  -25.0e6` follows the precedent `bp1001.fdc.rough.250` already set for the
  same EQdyna-vs-EQquasi sigma_n split (-50e6 vs -25e6) that rule 7's
  rationale documents; `nt_out = 20` likewise follows that precedent (EQdyna's
  value) over EQquasi's native 100. Verified independently of the dispatched
  agent's report: rule 8 gate re-run fresh (both compsets x both codes,
  pinned checkouts, all 4 writes + imports green), and the CLAUDE.md parity
  check re-derived (`on_fault_vars` bit-identical to EQquasi's own native
  compset `par` for both compsets; every remaining attribute diff accounted
  for). Found and logged as a new P3 row, not fixed here (rule 3): EQquasi's
  own `scripts/defaultParameters.py` hardcodes a personal `HPC_email`
  default that leaks into every machine=`local` generated output, including
  already-merged compsets -- pre-existing, not introduced by PR #49.
- 2026-10-16, filed per the above: before filing, ruled out an obvious source
  bug -- `gfortran -Wall -Wextra -Wuninitialized` at `-O3` on `netcdf_io.f90`
  flags nothing inside `netcdf_read_on_fault` (its one `-Wmaybe-uninitialized`
  hit is in the unrelated `netcdf_write`); `-fcheck=all` at `-O3` (bounds/
  pointer/recursion checks, no de-optimization) also does not fire, and a
  hybrid build with `netcdf_io.o` at `-O3 -fcheck=all` runs the stepover case
  400+ steps clean at full `-O3` speed, same as `-O2` (140+ steps clean) --
  both weigh against a plain OOB write as the cause. Per-flag bisection
  (`-fno-tree-vectorize` etc.) to pin the exact `-O3` sub-pass was not
  finished this session. Filed as EQquasi issue
  https://github.com/dunyuliu/EQquasi/issues/65 (pin `524a5236`,
  `netcdf_io.f90:420-456` inside `netcdf_read_on_fault` (377-502), GNU
  Fortran 15.3.0 conda-forge, netCDF-Fortran 4.6.4 / netCDF-C 4.10.1).

- 2026-10-16, closing the liu2020-compsets P3 row: re-ran `ls compset` on
  current `main` (`da3b832`), confirms `liu2020.fdc.planar.300` and
  `liu2020.fdc.rough.250` exist (landed PR #49, `e8b04d8`). Reads
  MEASURED-and-done per that re-run, not VERIFIED/validated -- no
  independent oracle exists for this problem, the same caveat the EQquasi
  native compset files already carry ("gate: none -- UNVERIFIED (no
  reference)").
- 2026-10-20, closing the stepover-fdc P1 row: pins moved to EQquasi
  `71f373e` (v1.21.4, mode 2 honors `par.nstep` above 30000) and EQdyna
  `15346fc` (EQdyna PR #231: mode-2 `fault.dyna.r.nc` carries
  `dip_node_spacing`, the owner decision of 2026-10-19). Reran
  `create.newcase fdc stepover2f-next test.stepover.2fault --machine local`,
  `par.iend = 2`, locally: both EQquasi cycles end on `exit_reason: stoptag`
  (cycle 1 at step 3867; cycle 2 at step 31374, 447 yr, peak 0.217 m/s, just
  past the old 30000 cap), both EQdyna cycles complete, all four handover
  files pass `check_handover.py` (ntotft=2, 12 vars), and both
  `fault.dyna.r.nc` carry `dip_node_spacing = 1000.0`. Rule 8 at the new
  pins: 10 of 10 generated compsets import; bp1001 EQquasi parity (machine
  ls6) differs only in `fric_pc_L` and `xcoor`, as CLAUDE.md allows.
- 2026-10-20, closing the `HPC_email` P3 row: at EQquasi `71f373e`,
  `scripts/defaultParameters.py:296` defaults `HPC_email` to `""`.

| Priority | Item | Command | Last checked |
|---|---|---|---|
| P1 | fdc on ls6 never run; locally `bp1001.fdc.rough.1000` ran two cycles for real (rerun 2026-10-13 with `fric_pc_L = Dc`) (`eqquasi-petsc` env, EQquasi `eqquasi-1.21.2` = pin source, EQdyna built at the pin): each EQquasi phase ended by handing over to EQdyna, and cycle 2's EQquasi started at peak slip rate 4.65613e-3 m/s, equal to the maximum in cycle 1's `fault.dyna.r.nc`. BLOCKED(owner): ls6 needs an MFA session ("Later") | `create.newcase fdc t bp1001.fdc.rough.1000 --machine ls6 && cd t && ./case.setup && ./case.submit` | 2026-10-13 |
| P2 | Normal-stress state-law length L: both codes now get the same explicit `par.fric_pc_L = par.fric_rsf_Dc` from `utils/convert.py` (PR #41; EQdyna takes it since pin `29774c3`, EQdyna PR #210); `_check_uniform_dc` still guards a non-uniform Dc. Left open upstream: EQdyna updates theta_pc explicitly for L > 0, EQquasi exponentially | rule 8 recipe (`PROJECT_RULES.md` rule 8), then `grep fric_pc_L <out>/*/*/user_defined_params.py` | 2026-10-16 |
| P2 | Pins in `components.txt` are recent heads (EQquasi `71f373e` 2026-10-19, EQdyna `15346fc` 2026-10-19), not the versions behind Liu et al. (2020): EQquasi's nearest-to-2020-12-31 commit is `66958e3` (2020-10-08), EQdyna's is `0381248` (2020-10-07) | `git -C components/eqquasi log --until=2020-12-31 -1` | 2026-10-20 |
| P3 | The 1 km low-pass (`roughness.resample`, Gaussian, 2 km cutoff) still passes about 37% amplitude at 2 km, the Nyquist wavelength of the 1 km grid; sharpen only if the owner asks | `grep -n "def resample" -A30 utils/roughness.py` | 2026-10-10 |
| P3 | EQdyna's own `case_input/bp1001.fdc.rough.250` is in the flat pre-`par` format its `case.setup` no longer imports (0 matches for `par = parameters`, reconfirmed at the current pin `15346fc`); filed as EQdyna issue https://github.com/EQDYNA/EQdyna/issues/222 | `grep -c 'par = parameters' components/eqdyna/case_input/bp1001.fdc.rough.250/user_defined_params.py` | 2026-10-20 |
| P3 | `utils/case.setup` rewrites two lines of EQquasi's `run.sh` (cycle loop, restart source) into `run.cycle.sh`, and stops if either line changes upstream | `create.newcase fdc t bp1001.fdc.rough.250 && cd t && ./case.setup` | 2026-10-09 |

Closed rows are in git history (`git log -p PATHWAY_FORWARD.md`).

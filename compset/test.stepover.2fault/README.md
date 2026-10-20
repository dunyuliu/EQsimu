# test.stepover.2fault

A planar two-fault releasing stepover (`ntotft = 2`), 1 km grid. It is not a
benchmark: it tests the multi-fault path of `utils/convert.py` for both codes.

![setup](setup.png)

| | |
|---|---|
| Faults | x −20…0 km at y = 0, and x −5…20 km at y = −2 km; both z −10…0 km |
| Friction | rate-and-state, aging law; velocity-weakening for \|z\| ≤ 7 km and ≥ 3 km from each fault end |
| Initial stress | σn = −25 MPa on fault 1, −27 MPa on fault 2 |
| Mode | fully dynamic (`par.mode = 2`); `create.newcase fdc` |
| Roughness | none; EQdyna refuses a rough fault with `ntotft > 1` |

The fdc settings (`exit_slip_rate`, `xi`, `C_normal_stress_caps`, `term`,
`dt`) are those of `bp1001.fdc.rough.250`.

## Results

Run locally with the pins of the time (EQquasi `524a5236`, EQdyna `29774c3`;
`--machine local`, 2026-10-11). Cycle 1
works: EQquasi reaches rupture on fault 1 after about 56 years, EQdyna runs
it to 150 s and hands back at peak slip rate 6.7e-4 m/s.

Cycle 2 used to stop within its first few steps with `STOP 508` reading
EQdyna's restart. Root cause: EQdyna hardwires its normal-stress state-law
length scale to the per-node Dc (no input for it); EQquasi's own `fric_pc_L`
defaulted to 0.0, which sets theta_pc = |sigma| instantly instead of
lagging it on EQdyna's timescale, so EQdyna's real restart state read as
inconsistent. Fixed in `utils/convert.py` (`par.fric_pc_L =
par.fric_rsf_Dc`, PR #22); upstream report on EQdyna:
https://github.com/EQDYNA/EQdyna/issues/189. Verified on a fresh fdc
rebuild (2026-10-12): cycle 2's EQquasi ran clean past 24,000+ steps / 350+
simulated years with no STOP/NaN/netCDF error. That case directory was
later deleted before cycle 2 handed over to EQdyna.

Two full cycles at the earlier pins (EQquasi `524a5236`, EQdyna `29774c3`),
local, 2026-10-18: all four handover files pass `check_handover.py`, with
normal-stress caps on. Cycle 1 ruptures at 58 years. Cycle 2's EQquasi ran
its full 30,000 steps (460 years, peak slip rate 0.02 m/s) without a second
rupture, because EQquasi then hardcoded `nstep = 30000` in fdc mode. EQquasi
must be built from a clean tree: objects left by a failed build crashed the
netCDF read (EQquasi #65, fixed upstream in PR #67).

Two full cycles at the pins EQquasi `71f373e` (v1.21.4, honors this
compset's `nstep = 200000`) and EQdyna `15346fc`, local, 2026-10-20: both
EQquasi phases end on a rupture (`exit_reason: stoptag`), cycle 1 at step
3867 and cycle 2 at step 31374 (447 years, peak slip rate 0.22 m/s). Both
EQdyna cycles complete, all four handover files pass `check_handover.py`, and
each `fault.dyna.r.nc` carries `dip_node_spacing`, which EQquasi >= 1.21.3
requires on a restart.

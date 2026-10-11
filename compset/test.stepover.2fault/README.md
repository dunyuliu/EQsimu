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

Run locally with the pinned codes (`--machine local`, 2026-10-11). Cycle 1
works: EQquasi reaches rupture on fault 1 after about 56 years, EQdyna runs
it to 150 s and hands back at peak slip rate 6.7e-4 m/s.

## Known issues

- Cycle 2 fails: EQquasi diverges within its first steps from EQdyna's
  `fault.dyna.r.nc` and stops with `STOP 508`. The trigger is fault 0's
  `effective_normal` alone: the rupture on fault 1 unclamps fault 0's
  stepover tip to −18.3 MPa (EQquasi's own file has −25 MPa there). With
  EQquasi's own `effective_normal` for fault 0 and everything else from
  EQdyna, the same restart runs. The restart layout of the two files is the
  same. The fix belongs in EQquasi's restart, not in EQsimu.

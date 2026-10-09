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

| Priority | Item | Command | Last checked |
|---|---|---|---|
| P1 | fdc never run with the pinned codes. BLOCKED(owner): no non-interactive ls6 access (MFA token required); needs the owner to open an ls6 session before a real build + one bp1001 cycle | `./checkout.sh -i ls6`, then `create.newcase fdc` + `./case.submit` | 2026-10-09 |
| P2 | Pins in `components.txt` are the 2026-10-09 heads, not the versions behind Liu et al. (2020) — confirmed: both pinned commits equal `origin/master` HEAD (0 ahead) in fresh read-only clones of both repos | `git -C <clone>/eqquasi rev-parse HEAD origin/master`; same for eqdyna | 2026-10-09 |
| P3 | EQdyna's own `case_input/bp1001.fdc.rough.250` is in the flat pre-`par` format that its `case.setup` no longer imports; report to EQdyna | `grep -c 'par = parameters' <clone>/eqdyna/case_input/bp1001.fdc.rough.250/user_defined_params.py` | 2026-10-09 |
| P3 | The liu2020 cases (`liu2020.fdc.planar`, `liu2020.fdc.rough.250` in both codes) are not yet EQsimu compsets | `ls compset` (only `bp1001.fdc.rough.250` present) | 2026-10-09 |
| P3 | `utils/case.setup` rewrites two lines of EQquasi's `run.sh` (cycle loop, restart source) into `run.cycle.sh`, and stops if either line changes upstream | `create.newcase fdc t bp1001.fdc.rough.250 && cd t && ./case.setup` | 2026-10-09 |
| — | 1 km bp1001 variant: slopes must come only from `roughness.write()`'s `np.gradient` on the 1 km heights (owner, verbatim above), verified against EQdyna's own geometry validator on the 1 km file. Open question needing owner confirmation before implementation: how the 1 km *heights* are derived from the 250 m `rough_heights.250.txt` — point-pick every 4th sample aliases wavelengths <2 km per Nyquist; a low-pass/block-average decimation is the careful alternative the owner's caution implies but did not name. Routed to Zofia to open as a scoped row pending that confirmation; show 1 km vs 250 m heights and slopes in the compset README once resolved. | `create.newcase` + EQdyna geometry validator on the 1 km file | 2026-10-09 |
| — | Stepover-to-fdc (mode 2, ntotft>1) is broken in both directions at the pins and neither code refuses it: EQquasi's `fault.r.nc` is untagged 3-D; EQdyna mode 2 reads tagged 2-D per-fault vars (`ft2_` for fault 2) and separately writes `fault.dyna.r_ft2.nc`; EQdyna also refuses `ntotft>1` with rough-surface input. Conversion side (problem to per-fault arrays) is doable in `utils/convert.py`; the restart-format bridge needs either an EQsimu-side netcdf reshape (new, greenfield, no reference — needs owner OK before dispatch) or upstream fixes (out of scope here per rule 3). Routed to Zofia to open as a scoped row; architecture choice held for owner sign-off. | read-only clone diff, this session | 2026-10-09 |

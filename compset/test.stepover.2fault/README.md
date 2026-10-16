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

2026-10-15 rerun attempt, at the current pins (EQquasi `524a5236`, EQdyna
`29774c3`), local, `eqquasi-petsc` conda env: BLOCKED in the build step,
before any case directory existed, so no handover files and no
`check_handover.py`/caps evidence were produced this attempt.
`./checkout.sh -i local` clones both codes then calls each one's own
`install.*.sh -m local`. EQquasi's `local` branch builds a private MUMPS
copy via `install.mumps.sh` (scivision/mumps, CMake+ninja). On this host
MUMPS's CMake `find_package(MPI)` resolves the system OpenMPI
(`/usr/lib/x86_64-linux-gnu/openmpi`, version 3.1) instead of the
`eqquasi-petsc` conda env's OpenMPI even with that env active and first on
`PATH`, and fails: `Could NOT find MPI (missing: MPI_Fortran_FOUND
Fortran)`. That leaves `mumps/build/local/include` without
`dmumps_struc.h`, and EQquasi's own `src/makefile` then fails compiling
`solveTimeLoopMUMPS.f90`: `Fatal Error: Cannot open included file
'dmumps_struc.h'`. Retried once, exporting `CC=$CONDA_PREFIX/bin/mpicc`,
`FC=$CONDA_PREFIX/bin/mpif90`, `CXX=$CONDA_PREFIX/bin/mpicxx`,
`MPI_HOME=$CONDA_PREFIX`, `CMAKE_PREFIX_PATH=$CONDA_PREFIX` before
`install.mumps.sh`: this got CMake's `find_package(MPI)` to pick the conda
env's MPI (`Found MPI_C:` / `Found MPI_Fortran:` both resolve to
`$CONDA_PREFIX/bin/mpicc`/`mpif90`, version 3.1), but MUMPS's own CMake
then fails a step later on LAPACK: `Could NOT find LAPACK (missing:
LAPACK_LIBRARIES)` (`cmake/FindLAPACK.cmake:489`), so `mumps/build` still
has no `Makefile`/`cmake_install.cmake`, `dmumps_struc.h` still does not
exist, and EQquasi's own build fails at the same
`solveTimeLoopMUMPS.f90`/`dmumps_struc.h` step as the first attempt. Not
retried further (two real, different, build-environment failures in a
row; stopping rather than chasing a third). This is an EQquasi/MUMPS
build-environment issue on this host, not an EQsimu bug (rule 3: EQsimu
never patches a checked-out component), so no source under `components/`
was touched, and no case directory, handover file, or caps evidence exists
from this attempt.

2026-10-15, second rerun attempt, same pins, fixing the MUMPS build by
calling EQquasi's own `-m conda-linux` install mode directly (not through
`checkout.sh -i local`, which cannot express a per-component mode):
`cd components/eqquasi && bash install.eqquasi.sh -m conda-linux` with
`eqquasi-petsc` active -- built in 5 s, no private MUMPS, linking the conda
env's `dmumps`/`lapack`/`scalapack`/`netcdf` directly
(`bin/eqquasi-1.21.2`). `EQDYNAROOT` pointed at a prebuilt EQdyna binary
already at the pin (`29774c3`), `EQQUASIROOT` at the fresh build; `PATH`
assembled to match `source checkout.sh`'s exports plus a `venv` ahead of it
for `scipy`/`netCDF4` (`create.newcase`'s `roughness.py` needs `scipy`,
absent from both conda envs on this host). `create.newcase fdc stepover2f
test.stepover.2fault --machine local` then `./case.setup` both succeeded
(case dirs for both codes fully populated; `case.setup` printed `normal-stress
caps ON: min_norm -10 MPa, max_norm -40 MPa`, confirming the PR #37/#40
setting is live in this case). `create.newcase` itself still exits 1 after
writing both case dirs -- `record()`'s `git -C $EQSIMUROOT rev-parse HEAD`
fails because this scratch copy of the EQsimu tree has no `.git` (an
artifact of the scratch area, not of the checked-in repo); cosmetic, both
case directories are complete regardless.

`./case.submit` then BLOCKED in cycle 0, before any rupture/handover:
EQquasi's first MPI rank fails reading `input/on_fault_vars_input.nc` --
`netCDF error: NetCDF: Invalid dimension ID or name while handling:
input/on_fault_vars_input.nc` -- immediately followed by a SIGSEGV in
another rank and `eqquasi exited 1 in cycle 0`. The file is
NETCDF4/HDF5 (`python3 -c 'import netCDF4; print(netCDF4.__version__)'`
-> 1.7.2, `file_format` `NETCDF4`, dimensions `fault`/`dip`/`strike`),
written by the `venv` Python's `netCDF4` package used for `create.newcase`;
EQquasi's Fortran netcdf reader is linked against the `eqquasi-petsc` conda
env's `netcdf-fortran`/`netcdf-c`/HDF5. This is a genuinely different
failure from the 2026-10-12 run (which read the same kind of file and ran
24,000+ clean steps) -- most likely an HDF5/netCDF library-version mismatch
between the `venv` that wrote the file and the conda env that reads it on
this specific host, not a build-flag issue and not something rule 3 permits
patching inside `components/eqquasi`. Not chased further (budget spent on
the build fix); no cycle-1 `fault.r.nc`, no cycle-1 `fault.dyna.r.nc`, no
cycle-2 handover, and no `check_handover.py`/caps-application evidence exist
from this attempt beyond the static `case.setup` confirmation above that
caps are configured ON.

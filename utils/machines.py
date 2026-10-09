"""
EQsimu's own machine registry: the machine-specific settings for a case,
selected by create.newcase's --machine flag and threaded through
utils/convert.py and utils/case.setup. Mirrors EQdyna's own
scripts/machines.py (scheduler + mpirun keys) since EQsimu wraps the same
launch question, one level up, for both codes together.

A problem (compset/<name>/user_defined_params.py) never hardcodes
HPC_ncpu/HPC_nnode/HPC_queue/HPC_time/HPC_account, or EQdyna's nx/ny/nz
process-grid (sized to EQdyna's own ncpu, not to the physics) -- those are
machine/launch settings, not part of the problem (PROJECT_RULES.md rule 7).
convert.write_code_compset merges MACHINES[name][code] into par.eqquasi /
par.eqdyna before generating that code's own user_defined_params.py.

Adding a machine means adding ONE entry below, with HPC_* (both codes) and
EQdyna's nx/ny/nz (so nx*ny*nz == eqdyna's own HPC_ncpu).

Fields per machine:
  scheduler   'slurm' or None (no batch scheduler -- utils/case.setup then
              runs each cycle's eqquasi/eqdyna body directly with bash,
              instead of `sbatch`-ing it).
  eqquasi     dict of HPC_ncpu/HPC_nnode/HPC_queue/HPC_time/HPC_account,
              merged into par.eqquasi.
  eqdyna      dict of HPC_ncpu/HPC_nnode/HPC_queue/HPC_time/HPC_account and
              nx/ny/nz, merged into par.eqdyna.
"""

MACHINES = {
    "ls6": dict(
        scheduler="slurm",
        eqquasi=dict(HPC_ncpu=30, HPC_nnode=1, HPC_queue="normal",
                     HPC_time="20:00:00", HPC_account="EAR22012"),
        eqdyna=dict(HPC_ncpu=128, HPC_nnode=2, HPC_queue="normal",
                    HPC_time="02:00:00", HPC_account="EAR22012",
                    nx=8, ny=4, nz=4),
    ),
    # No scheduler: direct mpirun, 6 cores for both codes (owner: "use 6
    # cores for both"). HPC_queue/HPC_time/HPC_account are never read by a
    # no-scheduler run (case.setup skips sbatch entirely), but each code's
    # own case.setup still writes them into an (unused) batch.hpc, so they
    # must be strings its own writer accepts, not None.
    "local": dict(
        scheduler=None,
        eqquasi=dict(HPC_ncpu=6, HPC_nnode=1, HPC_queue="normal",
                     HPC_time="00:10:00", HPC_account="local"),
        eqdyna=dict(HPC_ncpu=6, HPC_nnode=1, HPC_queue="normal",
                    HPC_time="00:10:00", HPC_account="local",
                    nx=6, ny=1, nz=1),
    ),
}


def machine(name):
    """The registry entry for `name`, or raise naming the known machines."""
    if name not in MACHINES:
        raise ValueError(
            "unknown machine %r (known: %s) -- add it to utils/machines.py's "
            "MACHINES table" % (name, ", ".join(sorted(MACHINES))))
    return MACHINES[name]

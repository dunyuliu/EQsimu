# EQsimu

Earthquake-cycle simulations with EQquasi (quasi-static, interseismic) and
EQdyna (dynamic rupture), coupled into fully dynamic cycles. Associated with
Liu et al. (2020).

EQsimu holds no solver code. It defines each **problem** once, in
`compset/<name>/user_defined_params.py`, and converts it into the
`user_defined_params.py` that EQquasi and EQdyna each read
(`utils/convert.py`). Fault roughness is built the same way: one surface on
the problem's fault grid, written as the `bFault_Rough_Geometry.txt` both
codes read (`utils/roughness.py`). Each code then runs its own workflow.

## Install

Requires Python 3 with `numpy`, `scipy`, and `netCDF4`
(`matplotlib` additionally for `utils/plot_problem.py`).

```
git clone https://github.com/dunyuliu/EQsimu.git
cd EQsimu
./checkout.sh -i ls6        # clone EQquasi + EQdyna at the commits in components.txt, build
source checkout.sh          # set EQSIMUROOT, EQQUASIROOT, EQDYNAROOT, PATH
```
`./checkout.sh -u ls6` moves existing checkouts to the pins and rebuilds.
On a workstation, `CONDA_PREFIX=<env> ./checkout.sh -i local` builds both
codes from a conda env made from EQquasi's `environment.yml` (no activation
needed), and adds `scipy` in `components/venv`, which `source checkout.sh` puts
first on `PATH`.

## Run a case

```
create.newcase MODE CASE COMPSET --machine MACHINE
```
| MODE | Code | |
|---|---|---|
| `qdc` | EQquasi | quasi-dynamic cycle |
| `dr`  | EQdyna | dynamic rupture |
| `fdc` | EQquasi + EQdyna | fully dynamic cycle; then `./case.setup && ./case.submit` in CASE |

`MACHINE` (see `utils/machines.py`) picks the HPC resources (ranks, nodes,
queue, wall time, account) and, for EQdyna, its process grid; `local` runs
without a scheduler, directly with `bash`/`mpirun`.

Example, a fully dynamic cycle on SEAS benchmark BP1001 at 1 km, small enough
for a workstation:
```
create.newcase fdc runs/fdc-bp1001 bp1001.fdc.rough.1000 --machine local
cd runs/fdc-bp1001 && ./case.setup && ./case.submit
```
`create.newcase` stages `CASE/eqquasi/` and `CASE/eqdyna/`, each a normal
case of that code, plus `CASE/eqsimu/` recording the problem and the commit
of EQsimu and of each code. `./case.setup` writes the per-cycle job chain;
`./case.submit` runs it. Results land in
`CASE/eqquasi/result/cycle<k>/` and `CASE/eqdyna/result/cycle<k>/`; cycles
run are `istart`-`iend` in `CASE/user_defined_params.py`.

## Problems

| Compset | |
|---|---|
| [`bp1001.fdc.rough.250`](compset/bp1001.fdc.rough.250/README.md) | SEAS BP1001, rough fault, 250 m |
| [`bp1001.fdc.rough.1000`](compset/bp1001.fdc.rough.1000/README.md) | the same problem at 1 km, for a local run |
| [`liu2020.fdc.planar.300`](compset/liu2020.fdc.planar.300/README.md) | Liu et al. (2020) cycle, planar fault, 300 m |
| [`liu2020.fdc.rough.250`](compset/liu2020.fdc.rough.250/README.md) | Liu et al. (2020) cycle, rough fault, 250 m |
| [`test.stepover.2fault`](compset/test.stepover.2fault/README.md) | planar two-fault stepover, tests the multi-fault conversion |

A new problem is a folder in `compset/` with a `user_defined_params.py`
(`par = problem()`, see `utils/problemDefaults.py`) and a README with
`setup.png` (`python3 utils/plot_problem.py compset/<name>`).

## Citing

Associated with Liu et al. (2020). Please cite that paper when using
EQsimu, EQquasi, or EQdyna.

## Getting help

Open a GitHub issue: https://github.com/dunyuliu/EQsimu/issues

## License

MIT — see [LICENSE](LICENSE).

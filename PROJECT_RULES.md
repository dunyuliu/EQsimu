# EQsimu Project Rules

Index:
1. Curated root — minimal changes, no stray files
2. Upstream components are the source of truth
3. No changes to EQdyna, EQquasi, or SORD from this repo
4. Reproducing paper-era results requires pinned component commits
5. No silent fallbacks or swallowed errors
6. A living status board
7. A problem is defined once, in `compset/`
8. `convert.py` changes are verified by importing every generated compset

---

## 1. Curated root — minimal changes, no stray files

Root is a whitelist: `checkout.sh`, `components.txt`,
`example.create.newcase.sh`, `README.md`, `CLAUDE.md`, `PATHWAY_FORWARD.md`,
`PROJECT_RULES.md`, `LICENSE`, `compset/`, `utils/`. Smallest edit that solves the problem; no new file
until an existing one can't hold it.

**Rationale**: EQsimu's value is being small enough to read in one sitting.

## 2. Upstream components are the source of truth

EQdyna, EQquasi, and SORD define solver behavior, install interfaces, and
input formats. When a wrapper assumption (binary path, flag, input format)
disagrees with what a component currently expects, the wrapper is wrong, not
the component.

**Rationale**: EQsimu has no authority over what a correct run looks like —
only over keeping up with it.

## 3. No changes to EQdyna, EQquasi, or SORD from this repo

No patch or local diff of a checked-out component is made or pushed from
here. Fixes go to that component's own repository.

**Rationale**: a clone treated as a place to fix things drifts invisibly
from upstream.

## 4. Reproducing paper-era results requires pinned component commits

`checkout.sh` checks out the commits in `components.txt`, and every case
records them in `eqsimu/components.txt`. Any reproduction claim names those
commits. Moving a pin is a commit to `components.txt`, with the parity check
in `CLAUDE.md` rerun.

**Rationale**: an unpinned dependency is a moving target.

## 5. No silent fallbacks or swallowed errors

Missing binary, failed install, or missing input fails loudly and stops the
checkout. Never `|| true`, never a stub copied into `bin/`.

**Rationale**: a `bin/` directory from a half-failed checkout can't be
trusted.

## 6. A living status board

`PATHWAY_FORWARD.md` at the repo root lists open gaps and stale assumptions,
each with a priority (P1/P2/P3), date last checked, and the command that
confirms it. One board; no second `TODO.md`/`STATUS.md` anywhere in the
tree.

**Rationale**: a wrapper tracking fast-moving upstream code needs an
explicit record of which assumptions are already known stale.

## 7. A problem is defined once, in `compset/`

Each problem lives in `compset/<name>/user_defined_params.py` with its
inputs and a README (`setup.png`, results). The codes'
`user_defined_params.py` are generated from it by `utils/convert.py` and are
never edited by hand. Code-specific settings go in `par.eqquasi` /
`par.eqdyna`; a parameter both codes read goes in the problem.

**Rationale**: the same case kept in two codes drifted (bp1001: σn −25 vs
−50 MPa), and nothing checked it.

## 8. `convert.py` changes are verified by importing every generated compset

Any change to `utils/convert.py`'s compset-loading or function-inlining logic
is verified by actually importing the generated `user_defined_params.py` for
every compset, for both EQquasi and EQdyna — not by checking a downstream
artifact (e.g. the geometry file) and inferring the Python import also works.

**Rationale**: a derived compset once lost its inlined `fault()` in both
generated files; the check had looked only at the geometry file.

**How to apply**: after touching `load_problem()`, `write_code_compset()`, or
any inlining/derivation path in `convert.py`, run, for each compset in
`compset/` and each of `eqquasi`/`eqdyna`:
`python3 -c "import convert; convert.write_code_compset('<compset>', '<code>', '<out>', 'local')"`
then `python3 -c "from user_defined_params import par"` against the generated
file, with `EQQUASIROOT`/`EQDYNAROOT` pointed at the pinned checkouts. A
derived-output check (geometry file, plot) is in addition to this, never
instead of it.

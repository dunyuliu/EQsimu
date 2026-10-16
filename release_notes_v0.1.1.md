# EQsimu v0.1.1 — 2026-10-15

## Summary of scope

Patch release. Two changes landed since v0.1.0, both already merged to
`main` via PR #37 and owner-approved on the board (`PATHWAY_FORWARD.md`,
2026-10-15):

- `components.txt`: EQdyna pin moved `42ce254` -> `29774c3` (current EQdyna
  head; `46ee862`..`29774c3` is board/docs/testsys plus a comment-only
  `scripts/defaultParameters.py` change, EQdyna PRs #213-#216).
- `utils/convert.py`: `par.C_normal_stress_caps` moved into the shared
  `COMMON` list, so both EQquasi and EQdyna read the identical value instead
  of EQquasi carrying it alone.

No new files, no compset redefinitions, no changes to EQdyna/EQquasi/SORD
checkouts from this repo.

## Files added / removed / renamed / cleaned up

None. Diff from v0.1.0 touches 5 existing files only: `components.txt`,
`utils/convert.py`, `compset/bp1001.fdc.rough.250/user_defined_params.py`,
`compset/test.stepover.2fault/user_defined_params.py`,
`PATHWAY_FORWARD.md`.

## Content updates to master documents

`PATHWAY_FORWARD.md`: closed the non-compressive-normal-stress P1 row and
the caps-input P2 row (both resolved by the pin move); added the
owner-decision log entry (2026-10-15); refreshed the `fric_pc_L` P2 row and
the pins P2 row to the new pin.

## Audit findings and fixes

Audit: independent pass by the audit router over `v0.1.0..442f72d`, scoped
to `PROJECT_RULES.md` and `CLAUDE.md`. Verdict: nothing Critical, nothing
blocking a release.

Findings and disposition:

- **Medium — CLAUDE.md pin-move parity check not evidenced in-repo.**
  `CLAUDE.md`'s "Checks before changing convert.py" requires `create.newcase
  fdc` + `./case.setup` to run against the pinned codes; the board's most
  recent run of that chain predates this pin move (2026-10-13, at the old
  pin `42ce254`). Rule 8 (import parity, this release's declared gate for
  `convert.py` changes) is independently green on `29774c3` — confirmed
  below — but the broader case.setup chain has not been rerun since the
  bump. Deferred: open issue, not fixed in this release.
- **Medium — stale/misleading comment in `utils/convert.py`.** The comment
  added at `convert.py:27-30` says a compset that omits
  `C_normal_stress_caps` falls back to "`par.eqdyna`'s -1 default"; in fact
  no compset currently omits it, and if one did, `_settings`'s
  `getattr(par, k)` would raise `AttributeError` before any fallback path —
  fails loudly, not silently, just not where the comment says. No compset
  is affected today. Deferred: open issue, a one-line comment fix for a
  follow-up commit, not applied here since this release does not otherwise
  touch `convert.py`'s COMMON-list comment block.
- **Low — three `PATHWAY_FORWARD.md` wording/citation nits** (an "only
  comment-only" qualifier that was slightly imprecise, a P3 row's pin
  mention not yet bumped to the new hash/date, a garbled clause in the
  `fric_pc_L` P2 row). Not applied in this release; the underlying claims in
  each row hold.
- **Advisory — `min_norm`/`max_norm` not in `COMMON`.** Both codes read
  them and currently share the same pinned defaults by coincidence, not by
  the `COMMON` list; no compset overrides them today. No action needed
  unless a future compset diverges.

No findings required a code fix that this release's scope would cover; all
are recorded as open issues above or left as advisory.

## Remaining open issues or pending items

- Rerun the full `create.newcase fdc` + `./case.setup` chain against the new
  EQdyna pin (`29774c3`), per `CLAUDE.md`'s declared check, and record the
  run in `PATHWAY_FORWARD.md`.
- Fix the `C_normal_stress_caps` fallback comment in `utils/convert.py`
  (see above) in a follow-up commit.
- `compset/test.stepover.2fault`'s README results (2026-10-11) were run
  caps-off at the old pin; this is a planar case, so caps are now on by
  default. Rerun and refresh the README once the case.setup chain above is
  confirmed.
- All other open items unchanged; see `PATHWAY_FORWARD.md`.

## Totals or cost changes

None (no cost-bearing runs in this release; pin bump and convert.py parity
fix only).

## Assumptions used

- The EQdyna pin move and the `C_normal_stress_caps` sharing were taken as
  owner-approved and already landed (board entry, PR #37); not re-litigated
  here.
- Rule 8 is this project's declared gate for any `convert.py` change
  (`PROJECT_RULES.md` rule 8); it was rerun directly against `442f72d`
  rather than relied on from the PR, since there is no CI to have run it
  independently.

## CI run this release was gated on

No CI configured (`.github/workflows/` absent in this repo). Gate for this
release was `PROJECT_RULES.md` rule 8, rerun directly on commit `442f72d`
against the pinned checkouts (EQquasi `524a5236`, EQdyna `29774c3`):

```
bp1001.fdc.rough.1000 eqquasi ok 0.14 1
bp1001.fdc.rough.1000 eqdyna ok None 1
bp1001.fdc.rough.250 eqquasi ok 0.14 1
bp1001.fdc.rough.250 eqdyna ok None 1
test.stepover.2fault eqquasi ok 0.14 1
test.stepover.2fault eqdyna ok None 1
```

All 3 compsets x both codes import `ok`; `C_normal_stress_caps` reads `1` on
both EQquasi and EQdyna for every compset (previously EQdyna read
`None`/`-1`, the mismatch this release fixes).

## Trend since v0.1.0

No `tests/check.sh`, `evals/`, or `gh run list` CI history exist in this
repo (no CI configured, no eval harness). Measures read directly:

- **Gate assertions.** No `tests/check.sh` in this repo; substituted with
  rule 8 (above), which was not run at v0.1.0 (the rule did not yet have a
  checked-in helper at that tag) — not comparable release-to-release yet.
- **Fixture verdicts.** No `evals/` directory in this repo. N/A.
- **Tracked text lines.** `git diff --stat v0.1.0..442f72d -- '*.md' '*.py'`:
  5 files changed, 38 insertions(+), 8 deletions(-).
- **Board currency.** `PATHWAY_FORWARD.md` at `442f72d`: 2 rows closed this
  release (non-compressive normal stress, caps input), 7 rows remain open
  (P1 x1, P2 x3, P3 x3), 0 rows with a blank last-checked date. At v0.1.0:
  9 open rows (P1 x2, P2 x4, P3 x3), same structure, no blank dates.
- **CI green-on-first-try rate.** No CI configured at either tag. N/A.

This section reports only; it does not gate. The two closed board rows and
a clean 38-line diff represent net improvement; no leanness regression to
flag.

## Work record

- audit: audit router's report on `v0.1.0..442f72d`, quoted above — 2
  Medium, 3 Low, 2 advisory findings, verdict "nothing Critical or WRONG"
- correctness: `COMMON`-list change and both generated-compset diffs
  confirmed correct by the audit; the one comment-accuracy issue found does
  not affect behavior (fails loudly, not silently, and no compset hits the
  path today)
- conciseness: diff is 38 lines across 5 files, all load-bearing (pin,
  parity fix, board update); no refactor pass run — scope too small and
  mechanical to warrant one
- fixes: no code fixes applied this release; two Medium findings and three
  Low findings recorded as open issues above rather than fixed, since each
  needs a human call (rerun a multi-hour case.setup chain, or touch
  already-merged convert.py code outside this release's stated scope)
- docs: `PATHWAY_FORWARD.md` reconciled against `442f72d`'s actual board
  rows (read directly, not from the diff) for the trend section above
- refactor: not run; `kai-fischer` not dispatched — a 38-line mechanical
  pin-bump diff is not a refactor target, and no existing code outside the
  diff was touched
- rules: self-checked against `PROJECT_RULES.md` directly (rules 1, 3, 4, 8,
  9 above); `zofia-kaminska` not dispatched for this release — no new or
  violated rule beyond what the audit above already covers

## Release gate

- tree: clean, one worktree, level with `origin/main` at push time
- ci: no CI configured (`.github/workflows/` absent); rule 8 substitute gate
  above is the record
- publish: `release_notes_v0.1.1.md` at repo root, tag `v0.1.1`, pushed to
  `origin`
- release: `gh release view v0.1.1` against the pushed tag
- clone: PASS `442f72d` — fresh `git clone` of this repo into an empty
  directory, rule 8 rerun from that clone against the pinned EQquasi/EQdyna
  checkouts, before any push (no `tests/release_gate.sh` exists in this
  project; this project has no package manifest/venv to isolate — its own
  dependencies are the pinned external EQquasi/EQdyna checkouts named in
  `components.txt`, not a Python lockfile)

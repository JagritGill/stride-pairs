# Working on stride-pairs

Read [README](README.md), [architecture](docs/architecture.md) and
[related work](docs/related-work.md). Purpose: bounded offline symbolic byte-layout
overlap evidence; never create real arrays or access process/device memory.

`stride_pairs/core.py` validates and enumerates logical elements, counts overlaps
with sorted endpoint searches, merges byte footprints and emits bounded witnesses.
`input.py` reads strict bounded JSON, `report.py` formats, `__main__.py` gates.
`tests/` holds an independent per-byte oracle and CLI/release regressions.
`scripts/` verifies examples and exact release scope. Python standard library only.

Release commands from this folder (record actual results at handoff):

```sh
python3 -B -m stride_pairs examples/repeated.json --limit 2
python3 -B -m stride_pairs examples/repeated.json --json --max-pairs 9
python3 -B -m unittest discover -s tests -v
python3 -B scripts/check_examples.py
python3 -B scripts/check_release.py
git diff --check
```

The second command intentionally exits 1. Valid ungated reports/pass gates exit 0;
invalid input/arguments exit 2 without a report. No static type checker/full linter
configured; syntax parsing is not typing. CI targets Python 3.13/3.15.

Invariants: all offsets/strides/itemsize are BYTES, not PyTorch stride units.
Half-open spans; mere touching is not overlap. Count logical pairs separately from
distinct bytes; repeated coordinates remain distinct elements. Empty dimensions
mean zero elements, empty shape means one scalar. Negative/zero strides supported
only within declared bounds. Witness order is left index then right index, both
lexicographic; changing evidence limit must not change exact totals. Preserve input.

Keep independent tests free of production addressing/count helpers. Add real CLI
regressions for parsing/gates and byte-oracle cases for model changes. Update the
allowlist deliberately for new files. Preserve owner changes and inspect status
before edits. No CodeRabbit, external reviewers, installs, credentials, private
traces, hardware, real memory access or automatic layout repairs. No backend,
dtype/alignment, write-safety or performance guarantees. Handoff exact commit,
checks and unrun limits; publication requires separate task authority.

# stride-pairs

Explain how two declared byte-strided array layouts overlap, without creating
arrays or reading memory. Exact counts distinguish **logical element pairs**,
**distinct shared bytes**, and **bounding-range overlap**. Bounded witnesses show
which index pairs intersect, including repeated and partial-span overlaps.

Useful when reviewing synthetic slicing, broadcasting or layout calculations.
Python 3.13/3.15 standard library only; no installation, NumPy, GPU or network.

## Quickstart

From this repository:

```sh
python3 -B -m stride_pairs examples/repeated.json --limit 2
```

Exact output:

```text
stride-pairs: symbolic byte-layout comparison
left: elements=6 unique_bytes=12 internal_pairs=3
right: elements=3 unique_bytes=12 internal_pairs=0
cross-view pairs=10 shared_bytes=10 extent_overlap_bytes=10
equal_span_pairs=0 different_span_pairs=10
left[0, 0] x right[0]: shared=[2, 4]
left[0, 1] x right[0]: shared=[4, 6]
witnesses_omitted=8
Metadata only; no arrays, values or memory are accessed.
```

The left layout repeats a three-element row through a zero stride. The right
layout is shifted by two bytes. No element spans are identical across the views,
yet ten pairs intersect. The left also has three internal unordered pairs sharing
bytes. Pair count is not a byte count; their equal values here are incidental.

```sh
python3 -B -m stride_pairs examples/repeated.json --json --max-pairs 9
python3 -B -m stride_pairs examples/repeated.json --max-pairs 10 --max-shared-bytes 10
python3 -B -m stride_pairs examples/interleaved.json --max-pairs 0
python3 -B -m stride_pairs examples/reversed.json --json
python3 -B -m stride_pairs examples/empty.json --json
```

First command intentionally exits **1**; the others exit **0**. Interleaved views
have 12 bytes of overlapping bounding extent but **zero addressed bytes in common**.
Reversed views share three identical spans under different coordinates. Empty
views cover no bytes. Zero strides can multiply pairs without increasing bytes.

## Input contract

```json
{"storage_bytes":16,
 "left":{"shape":[2,3],"strides":[0,4],"offset":0,"itemsize":4},
 "right":{"shape":[3],"strides":[4],"offset":2,"itemsize":4}}
```

Both views refer to the **same declared symbolic storage** [0,storage_bytes).
All strides, offsets and item sizes are **bytes**. An element at coordinate i
occupies [offset + sum(i[d]*strides[d]), start + itemsize). Touching endpoints
do not overlap. Negative/zero strides and partial overlaps are supported.
This is metadata arithmetic; offsets are not process pointers.

- Exactly the displayed fields; unknown/missing fields are rejected.
- Storage size integer 0..10^12; offset integer 0..storage_bytes.
- Shape/strides are flat lists of equal length, rank 0..6. Dimensions 0..2048;
  at most 2048 logical elements per view. Strides between -10^12 and 10^12.
- Item size integer 1..10^6. Nonempty views must fit fully within declared storage.
- An empty shape `[]` is one scalar. Any zero dimension is an empty view; its
  offset may equal storage size, and no element addresses are evaluated.
- Booleans, floats, duplicate JSON keys, non-finite numbers and unsupported forms
  are invalid. No inferred units, sorting, coercion, truncation or repair.
- CLI input: regular UTF-8 file <=32 KiB, no BOM or final symlink. Use stable trusted
  local paths; this is not a filesystem sandbox against concurrent replacement.

API, without file I/O:

```python
from stride_pairs import analyze

view = {"shape": [3], "strides": [0], "offset": 0, "itemsize": 4}
report = analyze({"storage_bytes": 4, "left": view, "right": view}, limit=1)
assert report["overlap"]["element_pairs"] == 9
assert report["overlap"]["shared_bytes"] == 4
assert report["left"]["internal_pairs"] == 3
```

`analyze` preserves input and raises `InputError` on unsupported metadata/limit.
API bounds equal CLI schema bounds, without the CLI file byte limit.

## Reports and gates

JSON schema version 1 includes each view's logical element count, distinct start
count, distinct byte count, half-open extent (null when empty), and internal
unordered overlapping pairs of **different logical elements**. Repetition remains
distinct even when two coordinates describe the same span.

`overlap` includes total cross-view pairs, equal-span versus different-span pairs,
counts of left/right elements with a partner, distinct shared bytes, and bounding
extent overlap bytes. Equal span means the same byte interval, not equal values
or compatible data types. Different spans include containment as well as partial
intersection. Internal pairs exclude pairing an element with itself; cross-view
pairs include every left/right coordinate combination, even identical metadata.

Witnesses are the first `--limit` overlapping pairs in left-index then right-index
lexicographic order, with both spans and their intersection. Default 5, range0..20.
`witnesses_omitted` is explicit; evidence limits never affect exact totals.
Reports expose supplied layout geometry, not array values; they are not anonymized.

Exit **0**: valid report and all supplied limits pass (or no limits supplied).
Exit **1**: `--max-pairs` or `--max-shared-bytes` exceeded, with report still emitted.
Limits are inclusive integers 0..10^12; both must pass if supplied. Gates concern
cross-view overlap only, not internal pairs. `--max-pairs 0` checks disjointness.
Exit **2**: invalid input/arguments, no report on stdout.

## Verification

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/check_examples.py
python3 -B scripts/check_release.py
git diff --check
```

Tests compare 3,600 small layout pairs and 200 seeded multidimensional cases to
independent per-byte sets. Boundaries, empty/scalar views, negative/zero strides,
partial overlap, witness limits and a 4,194,304-pair count case are covered.
Actual CLI and release-guard regression tests supplement the model oracle.
CI targets Python 3.13/3.15 on standard hosted runners with pinned actions.
No static checker/full linter configured; syntax parsing is not type checking.
Disclosure scanning is heuristic, not a guarantee.

See [architecture](docs/architecture.md), [related work](docs/related-work.md),
[AGENTS](AGENTS.md), [attribution](NOTICE.md) and [MIT license](LICENSE).
Independently implemented with Codex assistance; no global novelty or performance
claim. Machine-specific verification evidence remains outside this release.

## Limits

This tool does not discover real buffer identity or validate runtime metadata,
dtype, alignment, endianness, object references, backend stride support, concurrency
or write semantics. PyTorch strides are in elements; convert explicitly to bytes
before constructing this model. No real array construction, memory inspection,
hardware access, exploit demonstration or automatic layout change. No claim that
overlapping writes are safe, or that disjoint views make an entire program correct.
The finite logical-element cap trades scale for complete and explainable counts.

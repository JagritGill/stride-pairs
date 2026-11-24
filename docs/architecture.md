# Architecture and tradeoffs

[core.py](../stride_pairs/core.py) is pure metadata analysis;
[input.py](../stride_pairs/input.py) bounds and parses one local file;
[report.py](../stride_pairs/report.py) and [CLI](../stride_pairs/__main__.py) render
and apply gates. [Tests](../tests/test_core.py) independently materialize bytes on
small synthetic inputs. [Release guard](../scripts/check_release.py) verifies scope.

## Model

Both flat affine views address one declared symbolic byte domain. Each coordinate
maps to a fixed-width half-open interval. Duplicate starts remain different logical
elements, so broadcasting can increase pair counts without increasing footprint.
Zero-size dimensions are empty; rank zero is a scalar. Bounds are validated with
per-axis extrema before bounded coordinate enumeration. Negative strides contribute
to the minimum; positive strides to the maximum. No actual storage is allocated.

For each left interval [s,e), an overlapping right interval must start below e and
end above s. Binary searches in sorted right starts and ends count these intervals:
number of starts < e minus number of ends <= s. No cross-product is retained.
Repeating this operation against the same view counts directed self pairs; remove
one per element and divide by two for unordered internal pairs.

Equal-span frequencies classify cross pairs with exactly matching start and size.
Other intersections are different-span pairs, including strict containment. Union
merge of each view's intervals gives its unique footprint; a two-pointer traversal
intersects those unions to count distinct shared bytes. Bounding extents are
reported separately because holes can make their overlap misleading.

Only evidence generation checks individual candidate pairs. Visit left coordinates
then right coordinates in lexicographic order, skip left rows with zero partners,
and stop once the requested prefix is collected. Counts are independent of this
limit. Witnesses show both intervals and the exact intersecting half-open span.

## Bounds and complexity

With N/M <=2048 elements, rank<=6, and evidence limit K<=20, enumeration uses
O(N+M) records. Sorting/counting/footprint merge costs O((N+M) log(N+M)). Evidence
scans at most min(N,K) matching left rows across M right rows, plus the left-row
scan: O(N+min(N,K)*M). Report storage is O(K) beyond scalar summaries; working
storage O(N+M+K), with rank bounded. No loop runs per storage byte or numeric offset,
and no potentially four-million-entry cross-product is retained.

The 32-KiB file limit is independent of model bounds. Byte integers are <=10^12,
and output pairs <=2048^2, below common JSON exact-integer limits. Metadata files
must remain stable while read; no hostile-filesystem or concurrent snapshot claim.

## Tradeoffs and verification limits

This is not a general symbolic solver for arbitrarily large shapes, CuTe algebra,
NumPy/PyTorch adapter, optimizer or real-memory checker. An explicit cap makes
complete logical enumeration predictable. Bounds rejection identifies unsupported
metadata; the tool never demonstrates or performs an out-of-bounds access.

The test oracle walks each dimension recursively and represents actual addressed
byte sets for small inputs, then uses set intersections and Cartesian definitions.
It does not call production count, merge or addressing helpers. Larger boundary
tests use hand-derived invariants. Finite tests support this declared model only;
they do not establish backend write behavior, physical memory validity or speed.
See [research](related-work.md) for established concepts and nearest alternatives.

# Related work and provenance

Research completed November 24, 2026 before implementation. Queries included
`github tensor shape strides overlapping memory view analyzer tool numpy`,
`online tensor strides visualizer overlapping memory numpy as_strided`,
`github tensor stride visualizer memory layout overlap`,
`numpy shares_memory self overlap checker tool byte strides`,
`tensor byte overlap witness indices CLI layout alias auditor github` and
`"stride-pairs"`. Local and public personal catalogs had no matching project.
Search is not proof of name availability or worldwide uniqueness.

## Closest documented alternatives

- [NumPy shares_memory](https://numpy.org/doc/stable/reference/generated/numpy.shares_memory.html)
  checks whether actual arrays share storage, with an effort limit for difficult
  layouts. This is substantial overlap in the central question, not a new concept.
  [may_share_memory](https://numpy.org/doc/stable/reference/generated/numpy.may_share_memory.html)
  normally checks bounding extents and can report possible sharing where actual
  addressed bytes are disjoint. Our small model reports both extent overlap and
  exact shared byte count, element-pair counts and bounded coordinate witnesses.
- [tensor-layouts](https://github.com/jduprat/tensor-layouts) is a Python CuTe
  layout algebra with construction, composition and visualization, including
  logical-coordinate-to-offset mappings without a GPU. This is the closest broad
  educational layout tool; offline operation and mapping coordinates are shared
  ideas. We implement only two flat affine byte layouts, exposing pair-versus-byte
  multiplicity via a JSON/text CLI. No composition, tiling or GPU model is provided.
- [NumPy strides](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.strides.html)
  defines byte steps per dimension.
  [as_strided](https://numpy.org/doc/stable/reference/generated/numpy.lib.stride_tricks.as_strided.html)
  creates real views and documents self-overlap. Our inputs are symbolic metadata;
  no NumPy view, array storage or write operation is created.
- [PyTorch as_strided](https://docs.pytorch.org/docs/2.15/generated/torch.as_strided.html)
  makes real tensor views and documents overlap concerns. Its strides and storage
  offset use elements; this project's explicit byte units must not be confused
  with that API. We do not emulate backend support or tensor operation semantics.

These comparisons use official documentation and public READMEs. Search results
also exposed snippets from library implementations, but no snippets, source,
fixtures, tests, prose or diagrams were copied or translated. The comparisons are
not exhaustive feature inventories or claims that alternatives cannot do similar
analysis. No competitor software was installed or run.

## Concrete value and scope

The original demo describes six left logical elements, with a zero stride along
one axis, and three right elements shifted by two bytes. It has ten overlapping
cross-view element pairs but only ten distinct shared bytes; the left view also
has three internal overlapping pairs. A second example has overlapping extents
yet zero shared bytes. The distinction helps review indexing assumptions without
creating or modifying arrays. Partial-span overlap counts even if starts differ.

The existing portfolio's range-audit also uses interval reasoning, but accepts
explicit chunk ranges; it does not derive tensor coordinates, repeated logical
elements, self-pair counts or two-view pair witnesses. No substantive predecessor
implementation was copied. Affine addressing, interval merging and binary-search
counting are established ideas. This is a bounded explanatory tool, not a scalable
replacement for tensor libraries, memory inspection or a safety certification.

Original implementation, synthetic fixtures and tests are written from scratch
with Codex assistance. Routine portfolio release/input/CI conventions are reused
and credited in [NOTICE](../NOTICE.md). See [architecture](architecture.md) and
[README](../README.md) for exact semantics, resource bounds and limitations.

import copy
import itertools
import random
import unittest

from stride_pairs import InputError, analyze


def byte_elements(layout):
    # Independent small-model oracle: walk axes recursively, then materialize bytes.
    elements = []

    def walk(axis, index, address):
        if axis == len(layout['shape']):
            elements.append((list(index), set(range(address, address + layout['itemsize']))))
            return
        for number in range(layout['shape'][axis]):
            walk(axis + 1, index + (number,), address)
            address += layout['strides'][axis]

    walk(0, (), layout['offset'])
    return elements


def layout(shape, strides, offset=0, size=1):
    return dict(shape=shape, strides=strides, offset=offset, itemsize=size)


def document(left, right, storage=100):
    return dict(storage_bytes=storage, left=left, right=right)


def span(values):
    return [min(values), max(values)+1] if values else None


class CoreTests(unittest.TestCase):
    def compare(self, doc, limit=3):
        original = copy.deepcopy(doc)
        result = analyze(doc, limit)
        self.assertEqual(doc, original)
        left, right = byte_elements(doc['left']), byte_elements(doc['right'])
        sets = []
        for side, rows in [('left', left), ('right', right)]:
            union = set().union(*(b for _, b in rows))
            internal = sum(bool(a & b) for (_, a), (_, b) in itertools.combinations(rows, 2))
            self.assertEqual(result[side], dict(elements=len(rows), distinct_starts=len({min(b) for _, b in rows}),
                                               unique_bytes=len(union), extent=span(union), internal_pairs=internal))
            sets.append(union)
        pairs = [(li, lb, ri, rb) for li, lb in left for ri, rb in right if lb & rb]
        witnesses = [dict(left_index=li, right_index=ri, left_span=span(lb), right_span=span(rb), shared_span=span(lb & rb))
                     for li, lb, ri, rb in pairs[:limit]]
        equal = sum(lb == rb for _, lb, _, rb in pairs)
        bounds = [set(range(min(s), max(s)+1)) if s else set() for s in sets]
        self.assertEqual(result['overlap'], dict(element_pairs=len(pairs), equal_span_pairs=equal,
            different_span_pairs=len(pairs)-equal, shared_bytes=len(sets[0] & sets[1]),
            extent_overlap_bytes=len(bounds[0] & bounds[1]),
            left_elements_with_partner=len({tuple(li) for li, _, _, _ in pairs}),
            right_elements_with_partner=len({tuple(ri) for _, _, ri, _ in pairs}),
            witnesses=witnesses, witnesses_omitted=len(pairs)-len(witnesses)))
        return result

    def test_exhaustive_small_one_dimensional_pairs(self):
        candidates = []
        for n, step, size, offset in itertools.product(range(4), [-2, 0, 2], [1, 2], [0, 2, 4]):
            row = layout([n], [step], offset, size)
            elements = byte_elements(row)
            if all(all(0 <= byte < 6 for byte in data) for _, data in elements):
                candidates.append(row)
        for left in candidates:
            for right in candidates:
                self.compare(document(left, right, 6), 2)
        self.assertEqual(len(candidates), 60)  # 3,600 ordered layout pairs.

    def test_seeded_multidimensional_byte_oracle(self):
        rng = random.Random(20261124)
        for _ in range(200):
            rows = []
            for _ in range(2):
                shape = [rng.randrange(4) for _ in range(rng.randrange(4))]
                steps = [rng.randrange(-5, 6) for _ in shape]
                rows.append(layout(shape, steps, 40+rng.randrange(5), rng.randrange(1, 6)))
            self.compare(document(*rows), rng.randrange(6))

    def test_repeated_partial_overlap_demo(self):
        result = self.compare(document(layout([2, 3], [0, 4], size=4), layout([3], [4], 2, 4), 16))
        self.assertEqual(result['overlap']['element_pairs'], 10)
        self.assertEqual(result['overlap']['shared_bytes'], 10)
        self.assertEqual(result['left']['internal_pairs'], 3)
        self.assertEqual(result['overlap']['equal_span_pairs'], 0)

    def test_overlapping_extents_but_disjoint_bytes(self):
        result = self.compare(document(layout([4], [4], size=2), layout([4], [4], 2, 2), 16))
        self.assertEqual(result['overlap']['extent_overlap_bytes'], 12)
        self.assertEqual(result['overlap']['shared_bytes'], 0)

    def test_reverse_and_transpose_coordinates(self):
        self.compare(document(layout([3], [-4], 8, 4), layout([3], [4], 0, 4), 12))
        result = self.compare(document(layout([2, 3], [12, 4], size=4), layout([3, 2], [4, 12], size=4), 24))
        self.assertEqual(result['overlap']['equal_span_pairs'], 6)

    def test_touching_containment_and_internal_partial_spans(self):
        self.compare(document(layout([2], [2], size=3), layout([3], [1], 1, 1), 6))
        r = self.compare(document(layout([], [], size=2), layout([], [], 2, 2), 4))
        self.assertEqual(r['overlap']['element_pairs'], 0)

    def test_empty_scalar_and_singleton_axes(self):
        self.compare(document(layout([0, 2048], [-10**12, 10**12]), layout([0], [0]), 0))
        r = self.compare(document(layout([], [], 2, 2), layout([1, 1], [-10**12, 0], 2, 2), 4))
        self.assertEqual(r['overlap']['witnesses'][0]['left_index'], [])

    def test_limit_does_not_change_counts_or_prefix(self):
        doc = document(layout([5], [0], size=3), layout([5], [0], size=3))
        reference = analyze(doc, 20)
        for limit in [0, 1, 5, 20]:
            result = self.compare(doc, limit)
            self.assertEqual(result['overlap']['witnesses'], reference['overlap']['witnesses'][:limit])
            self.assertEqual(result['overlap']['element_pairs'], 25)

    def test_maximum_broadcast_and_huge_storage(self):
        row = layout([2048], [0], 10**12-10**6, 10**6)
        r = analyze(document(row, row, 10**12), 1)
        self.assertEqual(r['overlap']['element_pairs'], 4194304)
        self.assertEqual(r['overlap']['shared_bytes'], 10**6)
        self.assertEqual(r['left']['internal_pairs'], 2096128)
        self.assertEqual(r['overlap']['witnesses_omitted'], 4194303)

    def test_symmetry_and_translation(self):
        a, b = layout([3], [-3], 10, 4), layout([2, 2], [2, 0], 5, 3)
        first = analyze(document(a, b))
        second = analyze(document(b, a))
        for key in ['element_pairs', 'equal_span_pairs', 'different_span_pairs', 'shared_bytes', 'extent_overlap_bytes']:
            self.assertEqual(first['overlap'][key], second['overlap'][key])
        for row in [a, b]: row['offset'] += 10**10
        shifted = analyze(document(a, b, 10**12))
        for key in ['element_pairs', 'equal_span_pairs', 'shared_bytes']:
            self.assertEqual(first['overlap'][key], shifted['overlap'][key])

    def test_invalid_schema_types_rank_and_limits(self):
        scalar = layout([], [])
        invalid = [None, [], {}, dict(storage_bytes=True, left=scalar, right=scalar)]
        for key, value in [('shape', [2049]), ('shape', [2048, 2]), ('shape', [1]*7),
                           ('shape', [False]), ('shape', [1.0]), ('strides', [0]),
                           ('offset', -1), ('offset', 101), ('itemsize', 0), ('itemsize', 10**6+1)]:
            row = copy.deepcopy(scalar); row[key] = value; invalid.append(document(row, scalar))
        invalid += [document(layout([2048, 2], [0, 0]), scalar),
                    document(layout([2], [False]), scalar), document(layout([2], [10**12+1]), scalar),
                    document(dict(scalar, unknown=1), scalar), dict(document(scalar, scalar), extra=0)]
        for doc in invalid:
            with self.subTest(doc=doc), self.assertRaises(InputError): analyze(doc)
        for limit in [-1, 21, True, 1.0, '2']:
            with self.assertRaises(InputError): analyze(document(scalar, scalar), limit)

    def test_declared_storage_bounds(self):
        for row in [layout([2], [-1]), layout([2], [2], 0, 2), layout([], [], 3, 1)]:
            with self.assertRaises(InputError): analyze(document(row, layout([0], [0]), 3))
        self.compare(document(layout([2], [-1], 1), layout([], [], 2), 3))


if __name__ == '__main__':
    unittest.main()

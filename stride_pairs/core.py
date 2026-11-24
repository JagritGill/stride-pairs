"""Bounded symbolic affine byte layouts; never allocate or dereference storage."""

from bisect import bisect_left, bisect_right
from collections import Counter
from itertools import product
from math import prod

MAX_ELEMENTS = 2048
MAX_BYTES = 10**12


class InputError(ValueError):
    """Invalid metadata; messages do not echo supplied values."""


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _layout(value, storage, side):
    if type(value) is not dict or set(value) != {'shape', 'strides', 'offset', 'itemsize'}:
        raise InputError(f'{side}: expected shape, strides, offset and itemsize only')
    shape, strides = value['shape'], value['strides']
    if type(shape) is not list or not 0 <= len(shape) <= 6:
        raise InputError(f'{side}: shape must be a list of at most six dimensions')
    if type(strides) is not list or len(strides) != len(shape):
        raise InputError(f'{side}: strides must match shape rank')
    if not all(_integer(d, 0, MAX_ELEMENTS) for d in shape):
        raise InputError(f'{side}: dimensions must be integers from 0 through 2048')
    if not all(_integer(s, -MAX_BYTES, MAX_BYTES) for s in strides):
        raise InputError(f'{side}: strides must be bounded integer byte steps')
    count = prod(shape)
    if count > MAX_ELEMENTS:
        raise InputError(f'{side}: at most 2048 logical elements supported')
    offset, size = value['offset'], value['itemsize']
    if not _integer(offset, 0, storage) or not _integer(size, 1, 10**6):
        raise InputError(f'{side}: invalid byte offset or itemsize')
    if not count:
        return []
    travel = [(d - 1) * s for d, s in zip(shape, strides)]
    if offset + sum(min(0, t) for t in travel) < 0 or offset + sum(max(0, t) for t in travel) + size > storage:
        raise InputError(f'{side}: declared elements exceed symbolic storage bounds')
    return [(tuple(index), offset + sum(i*s for i, s in zip(index, strides)), size)
            for index in product(*(range(d) for d in shape))]


def _ranges(rows):
    merged = []
    for _, start, size in sorted(rows, key=lambda row: row[1]):
        end = start + size
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _counts(first, second):
    starts = sorted(start for _, start, _ in second)
    ends = sorted(start + size for _, start, size in second)
    # A half-open interval intersects [s,e) iff it starts before e and ends after s.
    return [bisect_left(starts, start + size) - bisect_right(ends, start)
            for _, start, size in first]


def _profile(rows):
    ranges = _ranges(rows)
    counts = _counts(rows, rows)
    return {'elements': len(rows), 'distinct_starts': len({s for _, s, _ in rows}),
            'unique_bytes': sum(b-a for a, b in ranges),
            'extent': [ranges[0][0], ranges[-1][1]] if ranges else None,
            'internal_pairs': (sum(counts) - len(rows)) // 2}, ranges


def _intersection_width(left, right):
    i = j = total = 0
    while i < len(left) and j < len(right):
        a, b = left[i], right[j]
        total += max(0, min(a[1], b[1]) - max(a[0], b[0]))
        if a[1] <= b[1]:
            i += 1
        else:
            j += 1
    return total


def analyze(document, limit=5):
    """Return exact counts and a bounded lexicographic prefix of pair evidence."""
    if not _integer(limit, 0, 20):
        raise InputError('evidence limit must be an integer from 0 through 20')
    if type(document) is not dict or set(document) != {'storage_bytes', 'left', 'right'}:
        raise InputError('expected exactly storage_bytes, left and right')
    storage = document['storage_bytes']
    if not _integer(storage, 0, MAX_BYTES):
        raise InputError('storage_bytes must be an integer from 0 through 1000000000000')
    left = _layout(document['left'], storage, 'left')
    right = _layout(document['right'], storage, 'right')
    left_profile, left_ranges = _profile(left)
    right_profile, right_ranges = _profile(right)
    left_counts, right_counts = _counts(left, right), _counts(right, left)
    pair_count = sum(left_counts)
    frequencies = Counter((start, size) for _, start, size in right)
    equal_pairs = sum(frequencies[(start, size)] for _, start, size in left)
    witnesses = []
    if pair_count and limit:
        for (li, ls, lw), matches in zip(left, left_counts):
            if not matches:
                continue
            for ri, rs, rw in right:
                low, high = max(ls, rs), min(ls+lw, rs+rw)
                if low < high:
                    witnesses.append({'left_index': list(li), 'right_index': list(ri),
                                      'left_span': [ls, ls+lw], 'right_span': [rs, rs+rw],
                                      'shared_span': [low, high]})
                    if len(witnesses) == limit:
                        break
            if len(witnesses) == limit:
                break
    extent_width = 0
    if left_profile['extent'] and right_profile['extent']:
        a, b = left_profile['extent'], right_profile['extent']
        extent_width = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    return {'schema_version': 1, 'storage_bytes': storage,
            'left': left_profile, 'right': right_profile,
            'overlap': {'element_pairs': pair_count, 'equal_span_pairs': equal_pairs,
                        'different_span_pairs': pair_count-equal_pairs,
                        'left_elements_with_partner': sum(n > 0 for n in left_counts),
                        'right_elements_with_partner': sum(n > 0 for n in right_counts),
                        'shared_bytes': _intersection_width(left_ranges, right_ranges),
                        'extent_overlap_bytes': extent_width,
                        'witnesses': witnesses, 'witnesses_omitted': pair_count-len(witnesses)}}

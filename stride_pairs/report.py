"""Deterministic text for bounded symbolic metadata."""


def render(report):
    overlap = report['overlap']
    lines = ['stride-pairs: symbolic byte-layout comparison']
    for side in ['left', 'right']:
        row = report[side]
        lines.append(f"{side}: elements={row['elements']} unique_bytes={row['unique_bytes']} internal_pairs={row['internal_pairs']}")
    lines.append(f"cross-view pairs={overlap['element_pairs']} shared_bytes={overlap['shared_bytes']} extent_overlap_bytes={overlap['extent_overlap_bytes']}")
    lines.append(f"equal_span_pairs={overlap['equal_span_pairs']} different_span_pairs={overlap['different_span_pairs']}")
    for row in overlap['witnesses']:
        lines.append(f"left{row['left_index']} x right{row['right_index']}: shared={row['shared_span']}")
    lines.append(f"witnesses_omitted={overlap['witnesses_omitted']}")
    lines.append('Metadata only; no arrays, values or memory are accessed.')
    return '\n'.join(lines)

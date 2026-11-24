"""Run checked-in examples and their intended CLI gate outcomes."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    cases = [
        (['examples/repeated.json', '--limit', '2'], 0, 10, 10, 10),
        (['examples/repeated.json', '--json', '--max-pairs', '9'], 1, 10, 10, 10),
        (['examples/repeated.json', '--max-pairs', '10', '--max-shared-bytes', '10'], 0, 10, 10, 10),
        (['examples/interleaved.json', '--max-pairs', '0'], 0, 0, 0, 12),
        (['examples/reversed.json', '--json'], 0, 3, 12, 12),
        (['examples/empty.json', '--json'], 0, 0, 0, 0),
        (['examples/repeated.json', '--json', '--limit', '0', '--max-shared-bytes', '9'], 1, 10, 10, 10),
        (['examples/reversed.json', '--json', '--max-shared-bytes', '12'], 0, 3, 12, 12),
    ]
    for arguments, status, pairs, shared, extent in cases:
        r = subprocess.run([sys.executable, '-B', '-m', 'stride_pairs', *arguments],
                           cwd=ROOT, capture_output=True, text=True, timeout=10)
        assert r.returncode == status and not r.stderr, (arguments, r.returncode, r.stderr)
        if '--json' in arguments:
            row = json.loads(r.stdout)['overlap']
            assert (row['element_pairs'], row['shared_bytes'], row['extent_overlap_bytes']) == (pairs, shared, extent)
        else:
            assert f'cross-view pairs={pairs} shared_bytes={shared} extent_overlap_bytes={extent}' in r.stdout
    print('8 CLI examples passed, including intentional gate exits 1')


if __name__ == '__main__':
    main()

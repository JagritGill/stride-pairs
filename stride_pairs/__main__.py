import argparse
import json
import sys
from . import InputError, analyze
from .input import load
from .report import render


def main(argv=None):
    parser = argparse.ArgumentParser(description='Compare two bounded symbolic byte-strided layouts.')
    parser.add_argument('metadata', help='local regular UTF-8 JSON file')
    parser.add_argument('--json', action='store_true', help='emit versioned JSON evidence')
    parser.add_argument('--limit', type=int, default=5, help='pair witnesses, 0..20 (default 5)')
    parser.add_argument('--max-pairs', type=int, help='inclusive cross-view overlapping element-pair limit')
    parser.add_argument('--max-shared-bytes', type=int, help='inclusive distinct shared byte limit')
    args = parser.parse_args(argv)
    try:
        for value in [args.max_pairs, args.max_shared_bytes]:
            if value is not None and not 0 <= value <= 10**12:
                raise InputError('gate limits must be integers from 0 through 1000000000000')
        report = analyze(load(args.metadata), args.limit)
    except InputError as exc:
        print(f'stride-pairs: invalid input: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2) if args.json else render(report))
    overlap = report['overlap']
    return int((args.max_pairs is not None and overlap['element_pairs'] > args.max_pairs) or
               (args.max_shared_bytes is not None and overlap['shared_bytes'] > args.max_shared_bytes))


if __name__ == '__main__':
    raise SystemExit(main())

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run([sys.executable, '-B', '-m', 'stride_pairs', *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=10)


class CliTests(unittest.TestCase):
    def test_reports_and_gate_boundaries(self):
        for flags, code in [((), 0), (('--max-pairs', '9'), 1), (('--max-pairs', '10'), 0),
                            (('--max-shared-bytes', '9'), 1), (('--max-pairs', '10', '--max-shared-bytes', '10'), 0)]:
            r = run('examples/repeated.json', '--json', '--limit', '0', *flags)
            self.assertEqual(r.returncode, code); self.assertEqual(r.stderr, '')
            self.assertEqual(json.loads(r.stdout)['overlap']['element_pairs'], 10)
        r = run('examples/interleaved.json', '--max-pairs', '0', '--max-shared-bytes', '0')
        self.assertEqual(r.returncode, 0); self.assertIn('shared_bytes=0', r.stdout)

    def bad(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, 'input.json'); path.write_bytes(data); result = run(path)
        self.assertEqual(result.returncode, 2); self.assertEqual(result.stdout, '')
        self.assertNotIn('Traceback', result.stderr)

    def test_json_parser_rejections(self):
        for value in [b'{', b'null', b'NaN', b'Infinity', b'1'*5000, b'['*2000+b']'*2000,
                      b'{"storage_bytes":1,"storage_bytes":2}', b'\xff', b'\xef\xbb\xbf{}']:
            self.bad(value)

    def test_file_size_exact_limit(self):
        data = (ROOT/'examples/empty.json').read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, 'input.json'); path.write_bytes(data+b' '*(32768-len(data)))
            self.assertEqual(run(path).returncode, 0)
        self.bad(data+b' '*(32769-len(data)))

    def test_file_kinds(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); path = root/'data'; path.write_text('{}')
            (root/'link').symlink_to(path); os.mkfifo(root/'fifo')
            for name in [root, root/'link', root/'fifo', root/'missing']:
                r = run(name); self.assertEqual(r.returncode, 2); self.assertEqual(r.stdout, '')

    def test_invalid_cli_arguments(self):
        for flags in [('--limit', '-1'), ('--limit', '21'), ('--limit', 'x'), ('--max-pairs', '-1'),
                      ('--max-shared-bytes', '1000000000001'), ('--unknown',)]:
            r = run('examples/empty.json', *flags)
            self.assertEqual(r.returncode, 2); self.assertEqual(r.stdout, '')

    def test_invalid_model_no_report(self):
        self.bad(b'{"storage_bytes":0,"left":{"shape":[],"strides":[],"offset":0,"itemsize":1},"right":{}}')


if __name__ == '__main__':
    unittest.main()

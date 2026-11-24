from pathlib import Path
import shutil
import tempfile
import unittest
from scripts.check_release import FILES, check

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        for name in FILES:
            target = self.root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, target)

    def test_exact_inventory(self):
        self.assertEqual(check(self.root)['files'], 22)
        extra = self.root/'extra'; extra.write_text('synthetic')
        with self.assertRaises(ValueError): check(self.root)
        extra.unlink(); (self.root/'LICENSE').unlink()
        with self.assertRaises(ValueError): check(self.root)

    def test_disclosure_negative_controls(self):
        target = self.root/'NOTICE.md'
        for sample in ['AK'+'IA'+'Z'*16, 'gh'+'p_'+'q'*36,
                       '/'+'Users'+'/synthetic/file', '-----BEGIN '+'RSA PRIVATE KEY-----']:
            target.write_text(sample)
            with self.assertRaises(ValueError): check(self.root)

    def test_links_modes_and_symlinks(self):
        target = self.root/'NOTICE.md'; target.write_text('[missing](missing.md)')
        with self.assertRaises(ValueError): check(self.root)
        target.write_text('safe'); target.chmod(0o755)
        with self.assertRaises(ValueError): check(self.root)
        target.unlink(); target.symlink_to(self.root/'README.md')
        with self.assertRaises(ValueError): check(self.root)

    def test_syntax_and_controls(self):
        target = self.root/'stride_pairs/__init__.py'; target.write_text('def (')
        with self.assertRaises(SyntaxError): check(self.root)
        target.write_text('"valid"\n'); (self.root/'NOTICE.md').write_bytes(b'x\x00')
        with self.assertRaises(ValueError): check(self.root)


if __name__ == '__main__':
    unittest.main()

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pixel_diet.cli import main


def _run(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = main(list(argv))
    return code, buf.getvalue().strip()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        a = np.zeros((32, 32, 3), dtype=np.uint8)
        b = a.copy()
        b[8:16, 8:20] = 255
        self.a, self.b = str(d / "a.png"), str(d / "b.png")
        Image.fromarray(a).save(self.a)
        Image.fromarray(b).save(self.b)

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_output_is_compact_json(self):
        code, out = _run("diff", self.a, self.b)
        self.assertEqual(code, 0)
        self.assertNotIn("\n", out)
        self.assertIn("regions", json.loads(out))

    def test_brief_is_one_line_with_verdict(self):
        code, out = _run("diff", self.a, self.b, "--brief", "--min-psnr", "40")
        self.assertEqual(code, 1)
        self.assertEqual(len(out.splitlines()), 1)
        self.assertTrue(out.startswith("FAIL diff"))
        self.assertIn("blob 12x8@8,8", out)

    def test_identical_images_pass_psnr_gate(self):
        # psnr_db is None (infinite) for identical images; that must not fail the gate.
        code, out = _run("diff", self.a, self.a, "--brief", "--min-psnr", "40")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("PASS diff psnr=inf"))

    def test_json_file_keeps_full_report(self):
        path = str(Path(self.tmp.name) / "r.json")
        _run("diff", self.a, self.b, "--brief", "--json", path)
        self.assertIn("mean_signed", json.loads(Path(path).read_text()))


if __name__ == "__main__":
    unittest.main()

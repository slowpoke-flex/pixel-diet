import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from pixel_diet import optimize, optimize_bytes, optimize_for_llm, optimize_tree, save
from pixel_diet.optimize import _trim_uniform, estimate_tokens


def framed(width: int = 640, height: int = 480, border: int = 80) -> Image.Image:
    im = Image.new("RGB", (width, height), (250, 250, 250))
    draw = ImageDraw.Draw(im)
    draw.rectangle((border, border, width - border - 1, height - border - 1), fill=(20, 30, 40))
    return im


def sprite() -> Image.Image:
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.rectangle((64, 80, 191, 199), fill=(200, 40, 30, 255))
    return im


class OptimizeTest(unittest.TestCase):
    def test_trim_uniform_crops_the_frame(self):
        im = framed()
        cropped = _trim_uniform(im, padding=0)
        self.assertLess(cropped.width, im.width)
        self.assertEqual(cropped.size, (480, 320))

    def test_ui_agent_caps_the_long_side(self):
        result = optimize(framed(1920, 1080, border=240), "ui-agent")
        self.assertLessEqual(max(result.width, result.height), 1280)
        self.assertEqual(result.format, "WEBP")
        self.assertGreater(result.token_ratio, 1.5)

    def test_ocr_document_is_grayscale_and_small(self):
        result = optimize(framed(1600, 2200, border=100), "ocr-document")
        out = Image.open(io.BytesIO(result.data))
        r, g, b = out.convert("RGB").getpixel((out.width // 2, out.height // 2))
        self.assertEqual((r, g, b), (r, r, r))  # grayscale, even if the WebP decoder reports RGB
        self.assertLessEqual(max(out.size), 1024)

    def test_game_sprite_crops_alpha_and_keeps_transparency(self):
        result = optimize(sprite(), "game-sprite")
        out = Image.open(io.BytesIO(result.data)).convert("RGBA")
        self.assertEqual(out.size, (128, 120))
        self.assertEqual(out.getpixel((0, 0)), (200, 40, 30, 255))  # the crop starts on the body, not on empty space

    def test_bytes_roundtrip_has_no_disk_io(self):
        buf = io.BytesIO()
        framed(800, 600).save(buf, "PNG")
        raw = buf.getvalue()
        out = optimize_bytes(raw, "ui-agent")
        self.assertIsInstance(out, bytes)
        self.assertLess(len(out), len(raw))
        self.assertEqual(Image.open(io.BytesIO(out)).format, "WEBP")

    def test_data_uri_is_ready_for_a_model(self):
        uri = optimize_for_llm(framed(400, 300), "ui-agent")
        self.assertTrue(uri.startswith("data:image/webp;base64,"))
        self.assertGreater(len(uri), 100)

    def test_save_writes_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "out" / "shot.webp"
            result = save(framed(500, 400), dst, "ui-agent")
            self.assertTrue(dst.exists())
            self.assertEqual(dst.stat().st_size, len(result.data))

    def test_optimize_tree_mirrors_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in"
            (src / "nested").mkdir(parents=True)
            framed(400, 300).save(src / "a.png")
            framed(400, 300).save(src / "nested" / "b.png")
            (src / "notes.txt").write_text("skip me", encoding="utf-8")
            report = optimize_tree(src, Path(tmp) / "out", "ui-agent")
            self.assertEqual(report["files"], 2)
            self.assertTrue((Path(tmp) / "out" / "a.webp").exists())
            self.assertTrue((Path(tmp) / "out" / "nested" / "b.webp").exists())
            self.assertFalse((Path(tmp) / "out" / "notes.txt").exists())

    def test_unknown_preset_is_rejected(self):
        with self.assertRaises(ValueError):
            optimize(framed(), "nope")

    def test_token_estimate_matches_the_formula(self):
        self.assertEqual(estimate_tokens(1920, 1080), 2765)
        self.assertEqual(estimate_tokens(1280, 720), 1229)


if __name__ == "__main__":
    unittest.main()

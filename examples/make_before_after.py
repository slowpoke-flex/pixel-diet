"""Build docs/shrink.png: the same screenshot before and after the ui-agent preset.

Both panels are displayed at the same width, so the eye compares legibility, not pixel count.
Run after changing a preset:  python examples/make_before_after.py
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pixel_diet import optimize
from shrink_demo import desktop_screenshot

HERE = Path(__file__).parent
DOCS = HERE.parent / "docs"
PANEL = 640
GAP = 32
PAD = 24
TOP = 48


def font(size: int = 20):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    original = desktop_screenshot()
    src = DOCS / "_before.png"
    original.save(src)
    source_bytes = src.stat().st_size

    result = optimize(src, "ui-agent")
    after = Image.open(io.BytesIO(result.data)).convert("RGB")
    src.unlink(missing_ok=True)

    left = original.resize((PANEL, round(PANEL * original.height / original.width)), Image.Resampling.LANCZOS)
    right = after.resize((PANEL, round(PANEL * after.height / after.width)), Image.Resampling.LANCZOS)

    body = max(left.height, right.height)
    canvas = Image.new("RGB", (PAD * 2 + PANEL * 2 + GAP, TOP + body + PAD), (10, 12, 16))
    canvas.paste(left, (PAD, TOP))
    canvas.paste(right, (PAD + PANEL + GAP, TOP))

    draw = ImageDraw.Draw(canvas)
    small = font(18)
    draw.text((PAD, 16), f"BEFORE  {original.width}x{original.height}  {source_bytes / 1024 / 1024:.2f} MB",
              fill=(255, 190, 120), font=small)
    draw.text((PAD + PANEL + GAP, 16),
              f"AFTER  {after.width}x{after.height}  {len(result.data) / 1024:.1f} KB",
              fill=(150, 220, 170), font=small)

    out = DOCS / "shrink.png"
    canvas.save(out, optimize=True)
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    print(f"tokens {result.tokens_before} -> {result.tokens_after} ({result.token_ratio}x)")


if __name__ == "__main__":
    main()

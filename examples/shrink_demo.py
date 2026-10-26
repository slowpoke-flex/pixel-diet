"""Generate three synthetic inputs and measure what every preset does to them.

These are not screenshots of a real product; they are deterministic stand-ins with the shapes that
matter (a UI with a solid frame, a document with margins, a sprite with transparent padding). Run:

    python examples/shrink_demo.py

It prints a table and writes the inputs and outputs under examples/shrink/ (ignored by git).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from pixel_diet import optimize

HERE = Path(__file__).parent
OUT = HERE / "shrink"


def ui_screenshot() -> Image.Image:
    """1920x1080, a solid 240 px frame around a busy middle: the 'refrigerator box' case."""
    im = Image.new("RGB", (1920, 1080), (246, 247, 249))
    d = ImageDraw.Draw(im)
    d.rectangle((240, 160, 1680, 920), fill=(255, 255, 255), outline=(214, 219, 226))
    d.rectangle((240, 160, 1680, 232), fill=(32, 38, 48))
    d.rectangle((272, 182, 520, 210), fill=(255, 255, 255))
    for row in range(6):
        y = 280 + row * 96
        d.rectangle((288, y, 420, y + 48), fill=(226, 231, 238))
        for col in range(4):
            x = 470 + col * 280
            d.rectangle((x, y, x + 240, y + 64), fill=(240, 243, 247), outline=(220, 225, 232))
            d.rectangle((x + 16, y + 16, x + 180, y + 30), fill=(120, 132, 148))
            d.rectangle((x + 16, y + 40, x + 140, y + 52), fill=(170, 180, 194))
    return im


def photo_wallpaper() -> Image.Image:
    """1920x1080 with a smooth gradient and mild noise: a realistic PNG that is megabytes, not kilobytes."""
    import numpy as np

    rng = np.random.default_rng(7)
    y, x = np.mgrid[0:1080, 0:1920]
    base = np.stack(
        [
            40 + 90 * (x / 1920) + 30 * np.sin(y / 240.0),
            60 + 70 * (y / 1080) + 20 * np.cos(x / 300.0),
            90 + 60 * ((x + y) / 3000.0),
        ],
        axis=-1,
    )
    base += rng.normal(0.0, 6.0, base.shape)
    return Image.fromarray(np.clip(base, 0, 255).astype("uint8"))


def desktop_screenshot() -> Image.Image:
    """A photo wallpaper with a UI panel and a solid window frame on top."""
    im = photo_wallpaper()
    d = ImageDraw.Draw(im)
    d.rectangle((320, 180, 1600, 940), fill=(252, 252, 253), outline=(210, 215, 222))
    d.rectangle((320, 180, 1600, 236), fill=(38, 44, 54))
    for row in range(5):
        y = 280 + row * 108
        d.rectangle((352, y, 560, y + 60), fill=(230, 234, 240))
        for col in range(3):
            x = 600 + col * 320
            d.rectangle((x, y, x + 280, y + 76), fill=(244, 246, 249), outline=(222, 226, 232))
            d.rectangle((x + 18, y + 18, x + 200, y + 34), fill=(120, 130, 146))
            d.rectangle((x + 18, y + 46, x + 160, y + 60), fill=(176, 184, 196))
    return im


def document() -> Image.Image:
    """A4 at 200 dpi with wide margins and grey text blocks."""
    im = Image.new("RGB", (1654, 2339), (252, 251, 248))
    d = ImageDraw.Draw(im)
    d.rectangle((210, 180, 900, 240), fill=(30, 30, 30))
    y = 320
    for block in range(26):
        width = 1180 if block % 7 else 760
        d.rectangle((210, y, 210 + width, y + 22), fill=(70, 70, 70))
        y += 46
        if block % 5 == 4:
            y += 40
    return im


def sprite() -> Image.Image:
    """512x512 RGBA with a 96 px transparent border and hard pixel edges."""
    im = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # body, head, two eyes and a shadow: flat colours, no anti-aliasing
    d.rectangle((160, 224, 352, 400), fill=(214, 92, 62, 255))
    d.rectangle((192, 128, 320, 224), fill=(238, 196, 148, 255))
    d.rectangle((216, 160, 240, 184), fill=(24, 24, 28, 255))
    d.rectangle((272, 160, 296, 184), fill=(24, 24, 28, 255))
    d.rectangle((208, 344, 304, 368), fill=(120, 40, 28, 255))
    d.rectangle((144, 400, 368, 416), fill=(0, 0, 0, 90))
    return im


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    samples = {
        "ui-flat.png": (ui_screenshot(), "ui-agent"),
        "desktop.png": (desktop_screenshot(), "ui-agent"),
        "document.png": (document(), "ocr-document"),
        "sprite.png": (sprite(), "game-sprite"),
        "camera.png": (ui_screenshot().resize((1600, 900)), "edge-fast"),
    }
    print(f"{'file':<14}{'preset':<14}{'pixels in':<14}{'pixels out':<14}"
          f"{'bytes in':<11}{'bytes out':<11}{'saved':<8}{'tokens':<9}ratio")
    for name, (image, preset) in samples.items():
        src = OUT / name
        image.save(src)
        result = optimize(src, preset)
        dst = OUT / (src.stem + "_out" + {"WEBP": ".webp", "PNG": ".png", "JPEG": ".jpg"}[result.format])
        dst.write_bytes(result.data)
        r = result.to_dict()
        print(f"{name:<14}{preset:<14}"
              f"{r['source_width']}x{r['source_height']:<7}"
              f"{r['width']}x{r['height']:<7}"
              f"{r['bytes_in'] / 1024:>8.1f}KB "
              f"{r['bytes_out'] / 1024:>8.1f}KB "
              f"{r['saved_pct']:>6.1f}% "
              f"{r['tokens_before']:>5}->{r['tokens_after']:<5}"
              f"{r['token_ratio']}x")


if __name__ == "__main__":
    main()

"""Turn a picture into the smallest picture that still answers the question.

Presets are the product: an agent or a pipeline should not tune fifteen thresholds. Every preset is a
short, named pipeline over Pillow's C primitives — no per-pixel Python loops.

Two entry points matter:

* ``optimize(path)`` / ``optimize_bytes(bytes)`` for code, with zero disk I/O in the bytes path;
* ``pixel-diet shrink`` for a shell, a cron job or a CI step.

Token estimates use the published Anthropic image formula ``ceil(w * h / 750)``. They are estimates,
not a bill; actual billing also depends on the provider, the model and the prompt.
"""

from __future__ import annotations

import base64
import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image, ImageChops, ImageOps

Source = str | Path | bytes | bytearray | io.BytesIO | Image.Image | np.ndarray

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}

_MIME = {"WEBP": "image/webp", "PNG": "image/png", "JPEG": "image/jpeg"}
_SUFFIX = {"WEBP": ".webp", "PNG": ".png", "JPEG": ".jpg"}
_RESAMPLE = {"lanczos": Image.Resampling.LANCZOS, "bilinear": Image.Resampling.BILINEAR, "nearest": Image.Resampling.NEAREST}


@dataclass(frozen=True, slots=True)
class Preset:
    """A named pipeline. Parameters are deliberately few and visible."""

    name: str
    summary: str
    trim: bool = False
    alpha_trim: bool = False
    grayscale: bool = False
    max_dimension: int = 1280
    fmt: str = "WEBP"
    quality: int = 80
    lossless: bool = False
    resample: str = "lanczos"


PRESETS: dict[str, Preset] = {
    "ui-agent": Preset(
        name="ui-agent",
        summary="crop solid borders, cap the long side at 1280 px, WebP q80",
        trim=True,
        max_dimension=1280,
        quality=80,
    ),
    "ocr-document": Preset(
        name="ocr-document",
        summary="crop uniform margins, grayscale, autocontrast, cap at 1024 px, WebP q85",
        trim=True,
        grayscale=True,
        max_dimension=1024,
        quality=85,
    ),
    "game-sprite": Preset(
        name="game-sprite",
        summary="crop the alpha bounding box, lossless WebP, no resampling",
        alpha_trim=True,
        max_dimension=4096,
        quality=100,
        lossless=True,
        resample="nearest",
    ),
    "edge-fast": Preset(
        name="edge-fast",
        summary="bilinear cap at 768 px, WebP q65, fastest encode",
        max_dimension=768,
        quality=65,
        resample="bilinear",
    ),
}

DEFAULT_PRESET = "ui-agent"


def estimate_tokens(width: int, height: int) -> int:
    """Anthropic-style image token estimate: one token per 750 pixels."""
    return max(1, math.ceil(width * height / 750))


@dataclass(frozen=True, slots=True)
class Result:
    data: bytes
    preset: str
    format: str
    width: int
    height: int
    source_width: int
    source_height: int
    source_bytes: int | None = None

    @property
    def mime(self) -> str:
        return _MIME[self.format]

    @property
    def data_uri(self) -> str:
        return f"data:{self.mime};base64," + base64.b64encode(self.data).decode("ascii")

    @property
    def bytes_out(self) -> int:
        return len(self.data)

    @property
    def saved_pct(self) -> float | None:
        if not self.source_bytes:
            return None
        return round(100.0 * (1.0 - self.bytes_out / self.source_bytes), 2)

    @property
    def tokens_before(self) -> int:
        return estimate_tokens(self.source_width, self.source_height)

    @property
    def tokens_after(self) -> int:
        return estimate_tokens(self.width, self.height)

    @property
    def token_ratio(self) -> float:
        return round(self.tokens_before / self.tokens_after, 2)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "preset": self.preset,
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "source_width": self.source_width,
            "source_height": self.source_height,
            "bytes_out": self.bytes_out,
            "tokens_after": self.tokens_after,
            "tokens_before": self.tokens_before,
            "token_ratio": self.token_ratio,
        }
        if self.source_bytes is not None:
            out["bytes_in"] = self.source_bytes
            out["saved_pct"] = self.saved_pct
        return out


def _load(src: Source) -> tuple[Image.Image, int | None]:
    """Open a path, bytes, BytesIO, ndarray or PIL image. Returns the image and its source size."""
    if isinstance(src, Image.Image):
        return src.copy(), None
    if isinstance(src, np.ndarray):
        return Image.fromarray(src), None
    if isinstance(src, (bytes, bytearray)):
        raw = bytes(src)
        return Image.open(io.BytesIO(raw)), len(raw)
    if isinstance(src, io.BytesIO):
        raw = src.getvalue()
        return Image.open(io.BytesIO(raw)), len(raw)
    path = Path(src)
    return Image.open(path), path.stat().st_size


def _trim_uniform(im: Image.Image, tolerance: int = 8, padding: int = 2) -> Image.Image:
    """Crop margins that are the same colour as the top-left pixel. C-speed, no Python loops."""
    rgb = im.convert("RGB")
    corner = rgb.getpixel((0, 0))
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, corner))
    r, g, b = diff.split()
    strongest = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mask = strongest.point(lambda v: 255 if v > tolerance else 0)
    box = mask.getbbox()
    if box is None:
        return im
    left, top, right, bottom = box
    left, top = max(0, left - padding), max(0, top - padding)
    right, bottom = min(im.width, right + padding), min(im.height, bottom + padding)
    if right - left < 8 or bottom - top < 8:
        return im
    return im.crop((left, top, right, bottom))


def _trim_alpha(im: Image.Image) -> Image.Image:
    """Pixel-exact crop to the non-transparent bounding box."""
    if im.mode not in ("RGBA", "LA"):
        im = im.convert("RGBA")
    box = im.getchannel("A").getbbox()
    return im.crop(box) if box else im


def _fit(im: Image.Image, max_dimension: int, resample: str) -> Image.Image:
    longest = max(im.size)
    if longest <= max_dimension:
        return im
    scale = max_dimension / longest
    size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
    return im.resize(size, _RESAMPLE[resample])


def _flatten(im: Image.Image) -> Image.Image:
    if im.mode in ("RGBA", "LA", "P"):
        rgba = im.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.getchannel("A"))
        return bg
    return im.convert("RGB")


def _encode(im: Image.Image, fmt: str, quality: int, lossless: bool) -> bytes:
    buf = io.BytesIO()
    if fmt == "WEBP":
        im.save(buf, "WEBP", quality=quality, lossless=lossless, method=6)
    elif fmt == "PNG":
        im.save(buf, "PNG", optimize=True)
    elif fmt == "JPEG":
        _flatten(im).save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    else:  # pragma: no cover - the CLI limits the choices
        raise ValueError(f"unsupported output format: {fmt}")
    return buf.getvalue()


def optimize(
    src: Source,
    preset: str = DEFAULT_PRESET,
    *,
    max_dimension: int | None = None,
    format: str | None = None,
    quality: int | None = None,
    trim: bool | None = None,
) -> Result:
    """Run a preset over one image and return the encoded bytes plus its numbers."""
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}; choose one of {', '.join(PRESETS)}")
    p = PRESETS[preset]
    im, source_bytes = _load(src)
    source_size = im.size
    im = ImageOps.exif_transpose(im)

    do_trim = (p.trim or p.alpha_trim) if trim is None else trim
    if p.alpha_trim and do_trim:
        im = _trim_alpha(im)
    elif do_trim:
        im = _trim_uniform(im)

    if p.grayscale:
        im = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)

    im = _fit(im, max_dimension or p.max_dimension, p.resample)

    out_fmt = (format or p.fmt).upper()
    q = p.quality if quality is None else quality
    lossless = p.lossless and quality is None and format is None
    data = _encode(im, out_fmt, q, lossless)

    return Result(
        data=data,
        preset=preset,
        format=out_fmt,
        width=im.width,
        height=im.height,
        source_width=source_size[0],
        source_height=source_size[1],
        source_bytes=source_bytes,
    )


def optimize_bytes(
    data: bytes,
    preset: str = DEFAULT_PRESET,
    *,
    max_dimension: int | None = None,
    format: str | None = None,
    quality: int | None = None,
    trim: bool | None = None,
) -> bytes:
    """In-memory path for webhooks and workers: bytes in, bytes out, no disk."""
    return optimize(
        data,
        preset,
        max_dimension=max_dimension,
        format=format,
        quality=quality,
        trim=trim,
    ).data


def optimize_for_llm(
    src: Source,
    preset: str = DEFAULT_PRESET,
    *,
    max_dimension: int | None = None,
    quality: int | None = None,
    trim: bool | None = None,
) -> str:
    """Return a ``data:`` URI ready for an OpenAI/Anthropic image content block."""
    return optimize(
        src,
        preset,
        max_dimension=max_dimension,
        quality=quality,
        trim=trim,
    ).data_uri


def save(
    src: Source,
    dst: str | Path,
    preset: str = DEFAULT_PRESET,
    **kwargs: Any,
) -> Result:
    """Optimize and write to ``dst``; the suffix is replaced to match the output format."""
    result = optimize(src, preset, **kwargs)
    path = Path(dst)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(result.data)
    return result


def optimize_tree(
    src_dir: str | Path,
    dst_dir: str | Path,
    preset: str = DEFAULT_PRESET,
    **kwargs: Any,
) -> dict[str, Any]:
    """Batch a directory, mirroring its structure. Hidden files and non-images are skipped."""
    root = Path(src_dir)
    out_root = Path(dst_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")

    fmt = (kwargs.get("format") or PRESETS[preset].fmt).upper()
    suffix = _SUFFIX[fmt]

    items: list[dict[str, Any]] = []
    bytes_in = 0
    bytes_out = 0
    tokens_before = 0
    tokens_after = 0
    for path in sorted(_iter_images(root)):
        rel = path.relative_to(root)
        target = out_root / rel.with_suffix(suffix)
        result = save(path, target, preset, **kwargs)
        bytes_in += result.source_bytes or 0
        bytes_out += result.bytes_out
        tokens_before += result.tokens_before
        tokens_after += result.tokens_after
        items.append({"input": str(rel), "output": str(target), **result.to_dict()})

    return {
        "preset": preset,
        "files": len(items),
        "bytes_in": bytes_in,
        "bytes_out": bytes_out,
        "saved_pct": round(100.0 * (1.0 - bytes_out / bytes_in), 2) if bytes_in else None,
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "token_ratio": round(tokens_before / tokens_after, 2) if tokens_after else None,
        "items": items,
    }


def _iter_images(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES and not path.name.startswith("."):
            yield path


def presets_table() -> str:
    """Plain-text preset table for ``--help`` and the README."""
    lines = [f"{'preset':<14}{'what it does':<74}max side"]
    for p in PRESETS.values():
        lines.append(f"{p.name:<14}{p.summary:<74}{p.max_dimension}")
    return "\n".join(lines)


def describe_preset(name: str) -> dict[str, Any]:
    p = PRESETS[name]
    return {
        "name": p.name,
        "summary": p.summary,
        "trim": p.trim,
        "alpha_trim": p.alpha_trim,
        "grayscale": p.grayscale,
        "max_dimension": p.max_dimension,
        "format": p.fmt,
        "quality": p.quality,
        "lossless": p.lossless,
        "resample": p.resample,
    }

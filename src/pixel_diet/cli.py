"""Command line interface for pixel-diet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from . import __version__
from .metrics import depth_metrics, diff_metrics, load_depth, load_image, load_mask, mask_metrics
from .optimize import (
    DEFAULT_PRESET,
    PRESETS,
    Result,
    optimize,
    optimize_tree,
    presets_table,
)


def _emit(args: argparse.Namespace, report: dict, verdict: str | None) -> None:
    """Write the full report to --json; print compact JSON, pretty JSON or a one-line brief."""
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.brief:
        print(_brief(args.cmd, report, verdict))
    elif args.pretty:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        # Compact by default: indentation costs ~35-40% more tokens for an agent reading stdout.
        print(json.dumps(report, separators=(",", ":"), ensure_ascii=False))


def _human(size: int | None) -> str:
    if size is None:
        return "?"
    if size < 1024:
        return f"{size}B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    return f"{size / (1024 * 1024):.2f}MB"


def _brief(cmd: str, r: dict, verdict: str | None) -> str:
    """One line, ~20-60 tokens: the verdict an agent needs before deciding to look closer."""
    head = f"{verdict} " if verdict else ""
    if cmd == "diff":
        psnr = "inf" if r["psnr_db"] is None else f"{r['psnr_db']:.2f}dB"
        regions = r["regions"][:3]
        reg = "; ".join(
            f"{x['kind']} {x['box'][2] - x['box'][0] + 1}x{x['box'][3] - x['box'][1] + 1}@{x['box'][0]},{x['box'][1]}"
            for x in regions
        )
        more = len(r["regions"]) - len(regions)
        reg += f"; +{more} more" if more > 0 else ""
        sheet = f" sheet={r['sheet']}" if "sheet" in r else ""
        return (f"{head}diff psnr={psnr} ssim={r['ssim']:.4f} changed={r['changed_pct']:.2f}% "
                f"regions={len(r['regions'])}" + (f": {reg}" if reg else "") + sheet)
    if cmd == "mask":
        worst = min(r["classes"], key=lambda c: c["iou"])
        return (f"{head}mask mean_iou={r['mean_iou']:.4f} mean_dice={r['mean_dice']:.4f} "
                f"worst=class {worst['class']} iou={worst['iou']:.4f}")
    if cmd == "shrink":
        if "files" in r:
            return (f"{head}shrink preset={r['preset']} files={r['files']} "
                    f"{_human(r['bytes_in'])}->{_human(r['bytes_out'])} ({r['saved_pct']}%) "
                    f"tokens~{r['tokens_before']}->{r['tokens_after']} ({r['token_ratio']}x)")
        return (f"{head}shrink preset={r['preset']} {r['source_width']}x{r['source_height']}"
                f"->{r['width']}x{r['height']} {r['format'].lower()} "
                f"{_human(r.get('bytes_in'))}->{_human(r['bytes_out'])} ({r.get('saved_pct')}%) "
                f"tokens~{r['tokens_before']}->{r['tokens_after']} ({r['token_ratio']}x)")
    return (f"{head}depth abs_rel={r['abs_rel']:.4f} rmse={r['rmse']:.4f} "
            f"d1={r['delta1']:.3f} valid_px={r['valid_px']}")


def _sheet(a_path: str, b_path: str, report: dict, out: str, width: int = 768) -> None:
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    # amplify the difference for the eye
    diff = diff.point(lambda v: min(255, v * 10))
    h = max(1, round(a.height * (width / 3) / a.width))
    panels = [im.resize((width // 3, h)) for im in (a, b, diff)]
    sheet = Image.new("RGB", (width, h), (10, 12, 16))
    for i, panel in enumerate(panels):
        sheet.paste(panel, (i * (width // 3), 0))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "A", fill=(255, 255, 255))
    draw.text((width // 3 + 8, 8), "B", fill=(255, 255, 255))
    draw.text((2 * (width // 3) + 8, 8), "|A-B| x10", fill=(255, 255, 255))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)


def _write_image(result: Result, target: str) -> str:
    if target == "-":
        sys.stdout.buffer.write(result.data)
        sys.stdout.buffer.flush()
        return "-"
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(result.data)
    return str(path)


def _run_shrink(args: argparse.Namespace) -> int:
    options = {
        "max_dimension": args.max_dimension,
        "format": args.format.upper() if args.format else None,
        "quality": args.quality,
        "trim": False if args.no_trim else None,
    }
    if args.input == "-":
        result = optimize(sys.stdin.buffer.read(), args.preset, **options)
        target = args.output
        if target != "-" and Path(target).is_dir():
            suffix = {"WEBP": ".webp", "PNG": ".png", "JPEG": ".jpg"}[result.format]
            target = str(Path(target) / ("stdin" + suffix))
        written = _write_image(result, target)
        report = {**result.to_dict(), "output": written}
    elif Path(args.input).is_dir():
        if args.output == "-":
            raise ValueError("a directory cannot be written to stdout; pass a directory to -o")
        report = optimize_tree(args.input, args.output, args.preset, **options)
    else:
        result = optimize(args.input, args.preset, **options)
        target = args.output
        if target != "-" and Path(target).is_dir():
            suffix = {"WEBP": ".webp", "PNG": ".png", "JPEG": ".jpg"}[result.format]
            target = str(Path(target) / (Path(args.input).stem + suffix))
        written = _write_image(result, target)
        report = {**result.to_dict(), "output": written}

    # Never mix text and binary on stdout.
    if args.output == "-":
        if args.json:
            Path(args.json).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 0
    _emit(args, report, None)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="pixel-diet",
        description="Put your agent on a pixel diet: shrink images before a vision model pays for them, "
                    "and compare images as numbers instead of pixels.",
        epilog=presets_table(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--version", action="version", version=f"pixel-diet {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", help="write the full pretty report to this path")
    out = common.add_mutually_exclusive_group()
    out.add_argument("--brief", action="store_true", help="print a one-line verdict instead of JSON")
    out.add_argument("--pretty", action="store_true", help="print indented JSON (default: compact)")

    s = sub.add_parser(
        "shrink",
        help="shrink an image or a folder for a vision model",
        description="Crop, resize and re-encode with a named preset. Accepts a file, a directory or - for stdin.",
        parents=[common],
    )
    s.add_argument("input", help="image, directory, or - for stdin")
    s.add_argument("-o", "--output", required=True, help="file, directory, or - for stdout")
    s.add_argument("--preset", default=DEFAULT_PRESET, choices=sorted(PRESETS))
    s.add_argument("--max-dimension", type=int, help="override the preset's longest side, in pixels")
    s.add_argument("--format", choices=["webp", "png", "jpeg"], help="override the preset's output format")
    s.add_argument("--quality", type=int, help="override the preset's quality (ignored for lossless presets)")
    s.add_argument("--no-trim", action="store_true", help="keep the borders, only resize and re-encode")

    d = sub.add_parser("diff", help="image / render difference", parents=[common])
    d.add_argument("a")
    d.add_argument("b")
    d.add_argument("--sheet")
    d.add_argument("--sheet-width", type=int, default=768, help="contact sheet width in px (smaller = cheaper)")
    d.add_argument("--threshold", type=float, default=0.02)
    d.add_argument("--min-psnr", type=float)

    m = sub.add_parser("mask", help="segmentation masks", parents=[common])
    m.add_argument("pred")
    m.add_argument("gt")
    m.add_argument("--classes", help="comma-separated class ids; default: all in gt")
    m.add_argument("--min-iou", type=float)

    p = sub.add_parser("depth", help="depth maps", parents=[common])
    p.add_argument("pred")
    p.add_argument("gt")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--max-absrel", type=float)

    sub.add_parser("presets", help="list the built-in presets")

    args = ap.parse_args(argv)
    if args.cmd == "presets":
        print(presets_table())
        return 0
    try:
        if args.cmd == "shrink":
            return _run_shrink(args)
        if args.cmd == "diff":
            report = diff_metrics(load_image(args.a), load_image(args.b), args.threshold)
            if args.sheet:
                _sheet(args.a, args.b, report, args.sheet, args.sheet_width)
                report["sheet"] = args.sheet
            failed = None
            if args.min_psnr is not None:
                # Identical images report psnr_db=None (infinite), which always passes.
                failed = report["psnr_db"] is not None and report["psnr_db"] < args.min_psnr
            _emit(args, report, _verdict(failed))
            if failed:
                return 1
        elif args.cmd == "mask":
            classes = [int(x) for x in args.classes.split(",")] if args.classes else None
            report = mask_metrics(load_mask(args.pred), load_mask(args.gt), classes)
            failed = None if args.min_iou is None else report["mean_iou"] < args.min_iou
            _emit(args, report, _verdict(failed))
            if failed:
                return 1
        else:
            report = depth_metrics(load_depth(args.pred), load_depth(args.gt), args.scale)
            failed = None if args.max_absrel is None else report["abs_rel"] > args.max_absrel
            _emit(args, report, _verdict(failed))
            if failed:
                return 1
    except Exception as exc:  # CLI: one line, non-zero
        print(f"pixel-diet: {exc}", file=sys.stderr)
        return 2
    return 0


def _verdict(failed: bool | None) -> str | None:
    return None if failed is None else ("FAIL" if failed else "PASS")


if __name__ == "__main__":
    raise SystemExit(main())

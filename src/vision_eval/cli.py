"""Command line interface for vision-eval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from .metrics import depth_metrics, diff_metrics, load_depth, load_image, load_mask, mask_metrics


def _write_json(path: str | None, report: dict) -> None:
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text + "\n", encoding="utf-8")
    print(text)


def _sheet(a_path: str, b_path: str, report: dict, out: str, width: int = 1200) -> None:
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="vision-eval", description="Numbers-first evaluation for computer vision.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("diff", help="image / render difference")
    d.add_argument("a")
    d.add_argument("b")
    d.add_argument("--json")
    d.add_argument("--sheet")
    d.add_argument("--threshold", type=float, default=0.02)
    d.add_argument("--min-psnr", type=float)

    m = sub.add_parser("mask", help="segmentation masks")
    m.add_argument("pred")
    m.add_argument("gt")
    m.add_argument("--classes", help="comma-separated class ids; default: all in gt")
    m.add_argument("--json")
    m.add_argument("--min-iou", type=float)

    p = sub.add_parser("depth", help="depth maps")
    p.add_argument("pred")
    p.add_argument("gt")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--json")
    p.add_argument("--max-absrel", type=float)

    args = ap.parse_args(argv)
    try:
        if args.cmd == "diff":
            report = diff_metrics(load_image(args.a), load_image(args.b), args.threshold)
            if args.sheet:
                _sheet(args.a, args.b, report, args.sheet)
                report["sheet"] = args.sheet
            _write_json(args.json, report)
            if args.min_psnr is not None and (report["psnr_db"] is None or report["psnr_db"] < args.min_psnr):
                return 1
        elif args.cmd == "mask":
            classes = [int(x) for x in args.classes.split(",")] if args.classes else None
            report = mask_metrics(load_mask(args.pred), load_mask(args.gt), classes)
            _write_json(args.json, report)
            if args.min_iou is not None and report["mean_iou"] < args.min_iou:
                return 1
        else:
            report = depth_metrics(load_depth(args.pred), load_depth(args.gt), args.scale)
            _write_json(args.json, report)
            if args.max_absrel is not None and report["abs_rel"] > args.max_absrel:
                return 1
    except Exception as exc:  # CLI: one line, non-zero
        print(f"vision-eval: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

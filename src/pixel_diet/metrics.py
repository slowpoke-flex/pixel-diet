"""Numeric image, mask and depth comparison. No model or framework dependencies."""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

Array = np.ndarray


def load_image(path: str | Path) -> Array:
    """RGB float32 in [0, 1]."""
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0


def load_mask(path: str | Path) -> Array:
    """Single-channel integer mask (class ids or 0/1). 0/255 PNG masks become 0/1."""
    with Image.open(path) as im:
        arr = np.asarray(im.convert("L"), dtype=np.int32)
    if arr.size and set(np.unique(arr)).issubset({0, 255}):
        arr //= 255
    return arr


def load_depth(path: str | Path) -> Array:
    """Single-channel float32 depth. 16-bit PNG and .npy are accepted."""
    if str(path).lower().endswith(".npy"):
        return np.asarray(np.load(path), dtype=np.float32)
    with Image.open(path) as im:
        if im.mode in ("I;16", "I;16B", "I;16L"):
            return np.asarray(im, dtype=np.float32) / 65535.0
        return np.asarray(im.convert("F"), dtype=np.float32)


def _as_rgb(a: Array) -> Array:
    if a.ndim == 2:
        return np.repeat(a[..., None], 3, axis=2)
    if a.shape[2] == 4:
        return a[..., :3]
    return a


def _check_same(a: Array, b: Array) -> None:
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}; resize explicitly before comparing")


def psnr(a: Array, b: Array, data_range: float = 1.0) -> float | None:
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    if mse == 0.0:
        return None  # identical; JSON has no infinity
    return float(10.0 * np.log10(data_range * data_range / mse))


def ssim(a: Array, b: Array, window: int = 7, data_range: float = 1.0) -> float:
    """Global mean of the local SSIM map (uniform window, per channel)."""
    a = _as_rgb(a).astype(np.float64)
    b = _as_rgb(b).astype(np.float64)
    _check_same(a, b)
    if window < 3 or window % 2 == 0:
        raise ValueError("window must be an odd number >= 3")
    c1 = (0.01 * data_range) ** 2
    c2 = (0.03 * data_range) ** 2
    values: list[float] = []
    from numpy.lib.stride_tricks import sliding_window_view

    for c in range(a.shape[2]):
        wa = sliding_window_view(a[..., c], (window, window))
        wb = sliding_window_view(b[..., c], (window, window))
        mu_a = wa.mean(axis=(-2, -1))
        mu_b = wb.mean(axis=(-2, -1))
        var_a = wa.var(axis=(-2, -1))
        var_b = wb.var(axis=(-2, -1))
        cov = ((wa - mu_a[..., None, None]) * (wb - mu_b[..., None, None])).mean(axis=(-2, -1))
        num = (2 * mu_a * mu_b + c1) * (2 * cov + c2)
        den = (mu_a**2 + mu_b**2 + c1) * (var_a + var_b + c2)
        values.append(float(np.mean(num / den)))
    return float(np.mean(values))


def _regions(mask: Array, diff: Array, limit: int = 12) -> list[dict[str, Any]]:
    """Connected components (4-neighbour) of the changed mask, largest first."""
    h, w = mask.shape
    if int(mask.sum()) > 250_000:
        return []  # avoid a slow Python flood fill on huge diffs
    seen = np.zeros_like(mask, dtype=bool)
    out: list[dict[str, Any]] = []
    peak = np.max(diff, axis=2) if diff.ndim == 3 else diff
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            area = 0
            x0 = x1 = x
            y0 = y1 = y
            p = 0.0
            while q:
                cy, cx = q.popleft()
                area += 1
                x0, x1 = min(x0, cx), max(x1, cx)
                y0, y1 = min(y0, cy), max(y1, cy)
                p = max(p, float(peak[cy, cx]))
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            kind = "blob"
            if area <= 4:
                kind = "speck"
            elif (x1 - x0) <= 2 or (y1 - y0) <= 2:
                kind = "line"
            out.append({"kind": kind, "area": area, "box": [int(x0), int(y0), int(x1), int(y1)], "peak": round(p, 4)})
    out.sort(key=lambda r: r["area"], reverse=True)
    return out[:limit]


def diff_metrics(a: Array, b: Array, threshold: float = 0.02) -> dict[str, Any]:
    a = _as_rgb(a).astype(np.float64)
    b = _as_rgb(b).astype(np.float64)
    _check_same(a, b)
    d = np.abs(a - b)
    changed = d.max(axis=2) > threshold
    return {
        "shape": list(a.shape),
        "mae": round(float(d.mean()), 6),
        "rmse": round(float(np.sqrt(np.mean((a - b) ** 2))), 6),
        "psnr_db": None if psnr(a, b) is None else round(psnr(a, b), 3),
        "ssim": round(ssim(a, b), 5),
        "changed_pct": round(float(changed.mean() * 100.0), 3),
        "max_abs": round(float(d.max()), 4),
        "mean_signed": round(float((a - b).mean()), 6),
        "threshold": threshold,
        "regions": _regions(changed, d),
    }


def mask_metrics(pred: Array, gt: Array, classes: list[int] | None = None) -> dict[str, Any]:
    _check_same(pred, gt)
    classes = classes if classes is not None else sorted(int(c) for c in np.unique(gt))
    per_class = []
    for c in classes:
        p = pred == c
        g = gt == c
        inter = int(np.logical_and(p, g).sum())
        union = int(np.logical_or(p, g).sum())
        pp = int(p.sum())
        gg = int(g.sum())
        iou = 1.0 if union == 0 else inter / union
        dice = 1.0 if (pp + gg) == 0 else 2 * inter / (pp + gg)
        precision = 1.0 if pp == 0 else inter / pp
        recall = 1.0 if gg == 0 else inter / gg
        per_class.append({"class": c, "iou": round(iou, 5), "dice": round(dice, 5),
                          "precision": round(precision, 5), "recall": round(recall, 5),
                          "pred_px": pp, "gt_px": gg})
    return {"classes": per_class, "mean_iou": round(float(np.mean([x["iou"] for x in per_class])), 5),
            "mean_dice": round(float(np.mean([x["dice"] for x in per_class])), 5)}


def depth_metrics(pred: Array, gt: Array, scale: float = 1.0) -> dict[str, Any]:
    _check_same(pred, gt)
    p = pred.astype(np.float64) * scale
    g = gt.astype(np.float64)
    valid = (g > 0) & np.isfinite(g) & np.isfinite(p)
    if not valid.any():
        raise ValueError("no valid depth pixels")
    p = p[valid]
    g = g[valid]
    abs_rel = float(np.mean(np.abs(p - g) / np.maximum(g, 1e-9)))
    rmse = float(np.sqrt(np.mean((p - g) ** 2)))
    ratio = np.maximum(p / np.maximum(g, 1e-9), g / np.maximum(p, 1e-9))
    return {"valid_px": int(valid.sum()), "abs_rel": round(abs_rel, 6), "rmse": round(rmse, 6),
            "delta1": round(float(np.mean(ratio < 1.25)), 5),
            "delta2": round(float(np.mean(ratio < 1.25**2)), 5),
            "delta3": round(float(np.mean(ratio < 1.25**3)), 5)}

"""Mind Space Studio pixel-diet: spend fewer tokens on the same picture.

Two halves of one idea:

* ``optimize`` / ``optimize_bytes`` / ``optimize_for_llm`` shrink an image before a vision model pays
  for it;
* ``diff_metrics`` / ``mask_metrics`` / ``depth_metrics`` turn a visual comparison into numbers, so the
  model does not have to look at both pictures.
"""

from .metrics import depth_metrics, diff_metrics, mask_metrics, psnr, ssim
from .optimize import (
    DEFAULT_PRESET,
    PRESETS,
    Result,
    estimate_tokens,
    optimize,
    optimize_bytes,
    optimize_for_llm,
    optimize_tree,
    save,
)

__all__ = [
    "diff_metrics",
    "mask_metrics",
    "depth_metrics",
    "psnr",
    "ssim",
    "optimize",
    "optimize_bytes",
    "optimize_for_llm",
    "optimize_tree",
    "save",
    "estimate_tokens",
    "Result",
    "PRESETS",
    "DEFAULT_PRESET",
]
__version__ = "0.3.0"

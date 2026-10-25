"""Estimate the context cost of reviewing an image pair: raw images vs the JSON report.

Usage:
    python examples/token_budget.py A.png B.png

Image cost uses Anthropic's published estimate (width * height / 750, long edge
capped at 1568 px, ~1600 tokens max per image). JSON cost uses tiktoken
cl100k_base as a proxy tokenizer when installed, otherwise ~4 chars per token.
Both are estimates; measure with your own model's token counter before quoting.
"""

import json
import subprocess
import sys

from PIL import Image


def image_tokens(path: str) -> int:
    w, h = Image.open(path).size
    scale = min(1.0, 1568 / max(w, h))
    return min(round(w * scale * h * scale / 750), 1600)


def text_tokens(text: str) -> int:
    try:
        import tiktoken

        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except ImportError:
        return round(len(text) / 4)


def main() -> None:
    a, b = sys.argv[1], sys.argv[2]
    # Exit code 1 (threshold failed) still produces a valid report.
    out = subprocess.run(
        [sys.executable, "-m", "vision_eval", "diff", a, b],
        capture_output=True,
        text=True,
    ).stdout
    report = json.loads(out)
    pair = image_tokens(a) + image_tokens(b)
    js = text_tokens(json.dumps(report, indent=2))
    print(f"images A+B : ~{pair} tokens")
    print(f"JSON report: ~{js} tokens")
    print(f"ratio      : ~{pair / max(js, 1):.1f}x")


if __name__ == "__main__":
    main()

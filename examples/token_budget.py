"""Estimate the context cost of reviewing an image pair: raw images vs the JSON report.

Usage:
    python examples/token_budget.py A.png B.png

Image cost uses Anthropic's published estimate (width * height / 750, long edge
capped at 1568 px, ~1600 tokens max per image). JSON cost uses tiktoken
cl100k_base as a proxy tokenizer when installed, otherwise ~4 chars per token.
Both are estimates; measure with your own model's token counter before quoting.
"""

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

    def run(*extra: str) -> str:
        # Exit code 1 (threshold failed) still produces valid output.
        cmd = [sys.executable, "-m", "pixel_diet", "diff", a, b, *extra]
        return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

    pair = image_tokens(a) + image_tokens(b)
    rows = [
        ("pretty JSON  (--pretty)", text_tokens(run("--pretty"))),
        ("compact JSON (default)", text_tokens(run())),
        ("one line     (--brief)", text_tokens(run("--brief"))),
    ]
    print(f"{'images A+B':<24}: ~{pair} tokens")
    for name, n in rows:
        print(f"{name:<24}: ~{n} tokens  (~{pair / max(n, 1):.0f}x fewer)")


if __name__ == "__main__":
    main()

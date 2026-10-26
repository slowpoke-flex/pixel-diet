# Publish checklist (owner only)

The repository is a normal Python package and an agent skill. The public face is **Mind Space Studio**;
do not mention `the private product brand`, the engine, private data or customer names.

## Before `git push`

- [ ] `python -m unittest discover -s tests` → OK (19 tests).
- [ ] `python examples/shrink_demo.py` → the table matches `README.md`.
- [ ] `pixel-diet presets` works, and `pixel-diet shrink` works on a file, a directory and stdin.
- [ ] `README.md`, `README.zh-CN.md`, `README.ru.md` describe the same presets and the same numbers.
- [ ] `LICENSE` says MIT, Mind Space Studio, 2026.
- [ ] `git grep -nE "sk-|AIza|ghp_|PRIVATE KEY|[A-Z]:\\\\Users"` returns nothing.
- [ ] No `Private/`, `.env`, tokens, customer images or salary data.
- [ ] Token estimates are labelled as estimates; no "identical output" claim.

## Release

`gh` is installed at `C:\Program Files\GitHub CLI\gh.exe` and authenticated as `slowpoke-flex`.

```bash
cd "C:\Mind Space Studio\public\pixel-diet"
git tag -a v0.3.0 -m "pixel-diet 0.3.0: presets, bytes API, batch CLI"
git push origin main --tags
gh release create v0.3.0 --title "pixel-diet 0.3.0" --notes "Presets (ui-agent, ocr-document, game-sprite, edge-fast), path/bytes/data-URI API, batch and stdin CLI, measured table, 19 tests."
```

## PyPI (not done yet)

The name `pixel-diet` is free on PyPI as of 2026-10-26. Publishing needs an account and a token:

```bash
python -m pip install build twine
python -m build
twine upload dist/*
```

Do not write `pip install pixel-diet` in the README until the upload exists.

## Topics and description

Description:

> Shrink images before a vision model pays for them: crop, resize and re-encode with named presets. Compares images as numbers too.

Add the 20 topics from `docs/github-topics.md`. Topics are a hint; the measured table and community posts
are the distribution.

## The duplicate question

`slowpoke-flex/vision-eval` shares this repository's history and describes the old, evaluation-only product.
Two public repos with the same code and the same 20 topics split attention and look careless. Decide one:

- keep `pixel-diet` public and make `vision-eval` private (one command, reversible), or
- keep both and make `vision-eval` a thin pointer to `pixel-diet`.

Do not leave both as full copies.

## What this does not prove

This repository is a **studio utility**, not a proof of the engine project. It can show that the studio measures
before it claims; it does not replace the engine gate, the public facade or the first customer.

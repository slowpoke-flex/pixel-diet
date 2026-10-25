# Publish checklist (owner only)

The repository is a normal Python package and an agent skill. It is **not** NewWave3D; do not mention
`.newwave3d`, the engine, private data or customer names. The public face is **Mind Space Studio**.

## Before `git push`

- [ ] `python -m unittest discover -s tests` → OK.
- [ ] `python examples/make_examples.py` → files generated.
- [ ] `python -m vision_eval diff examples/a.png examples/b.png --json /tmp/r.json --sheet /tmp/s.png` → works.
- [ ] `python -m pip install -e .` → `vision-eval --help` works.
- [ ] `docs/demo.png` is a real screenshot of the diff sheet.
- [ ] `README.md`, `README.zh-CN.md`, `README.ru.md` are present and linked.
- [ ] `LICENSE` says MIT, Mind Space Studio, 2026.
- [ ] `git grep -nE "sk-|AIza|ghp_|PRIVATE KEY|C:\\\\Users|NewEra3D"` returns nothing.
- [ ] No `Private/`, `.env`, tokens, customer images or personal salary data.

## Create the repository

`gh` is not installed on the current laptop. Install it (`winget install --id GitHub.cli`), then:

```bash
gh auth login
cd "C:\Mind Space Studio\public\vision-eval"
git init -b main
git add .
git commit -m "vision-eval: numbers-first evaluation for computer vision"
gh repo create <owner>/vision-eval --public --source . --remote origin --push
```

If the studio has an organisation, use `<org>/vision-eval`; otherwise the owner account is fine, the README
still says Mind Space Studio.

## Topics and description

Description:

> Numbers-first computer-vision evaluation: image diffs, masks, depth, contact sheets, agent skill.

Add the 20 topics from `docs/github-topics.md` in **Settings → Topics**. Topics are a hint; the README,
examples and community posts are the distribution.

## Optional GitHub Pages

A repository README is already a page. If a landing page is wanted, enable **Settings → Pages → Deploy from
branch → main /docs** only after adding `docs/index.html`; do not publish the engine or private demos there.

## Distribution

Follow `LAUNCH.md`. The first goal is 10 users who ran it on their own data, not 1,000 stars. Do not buy stars,
fake testimonials or post the same text in ten communities.

## What this does not prove

This repository is a **studio utility**, not a proof of NewWave3D. It can show that the studio writes honest
tooling; it does not replace the engine gate, the public facade or the first customer.

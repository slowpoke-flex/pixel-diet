# Launch plan

This is not a promise of stars. Stars are a lagging indicator; the first goal is **ten real users** who ran
the tool on their own images and told us what broke.

## Before public

- [ ] `python -m unittest discover -s tests` passes.
- [ ] `python examples/make_examples.py` and all three commands run.
- [ ] README screenshots/GIF are real output, not mockups.
- [ ] No internal paths, customer data, API keys or `.newwave3d` branding.
- [ ] MIT license and studio name are correct.
- [ ] Repository is under the studio account, not a personal dump.

## Week 1

1. Publish the repo with topics from `docs/github-topics.md`.
2. Publish the package to PyPI (`python -m build`, `twine upload`).
3. Post a 60-second demo: one image pair, one failing region, one JSON report.
4. Submit to 3 relevant awesome lists (computer vision, AI agents, Claude/Codex tooling). Read each list's rules.
5. Post where CV engineers actually are: r/computervision, r/MachineLearning, r/LLMDevs, Show HN, a Chinese
   Zhihu/WeChat note, a Russian Habr/Telegram note. One post per community, not a blast.
6. Ask 10 CV engineers for one failure case; turn the best into `examples/`.

## What not to do

- Do not buy stars, use bots, or ask friends to star without using it.
- Do not claim it improves a model; it measures outputs.
- Do not call it a NewWave3D proof; it is a studio utility.
- Do not add 20 unrelated trending topics.

## Good first issues

- Add FLIP support when `flip-eval` is installed.
- Add COCO/YOLO box metrics (`pixel-diet boxes`).
- Add a boundary-F score for masks.
- Add a GitHub Action that comments the JSON on a PR.
- Add a Chinese/Russian README fix from a native speaker.

## Success check after 30 days

- 10+ unique users who ran it on their own data.
- 3 issues or PRs from outside the studio.
- 1 CV engineer who says "this caught a bug I would have missed".
- Stars are a bonus, not the goal.

# Launch plan

Stars are a lagging indicator. The first goal is **ten people who shrank their own screenshots and told us
what broke**. The second is one public before/after with real numbers from someone else's workload.

## Before public

- [ ] `python -m unittest discover -s tests` passes (19 tests).
- [ ] `python examples/shrink_demo.py` prints the table in the README.
- [ ] `python -m pip install -e .` then `pixel-diet presets` works.
- [ ] README numbers match the demo output on the machine that ships.
- [ ] No internal paths, customer data, API keys or `the private product brand` branding.
- [ ] The repo says clearly: token counts are estimates, shrinking is lossy.

## The only demo that matters

One 1920×1080 screenshot with a lot of dead space, one command, one JSON line:

```text
shrink preset=ui-agent 1920x1080->1280x720 webp 2.08MB->9.6KB (99.55%) tokens~2765->1229 (2.25x)
```

Show the shrunk image next to the original at the same display size. If the text is unreadable, the demo
failed — say so and pick a different preset. Do not show a 4K wallpaper as a "typical screenshot".

## Week 1

1. Publish `v0.3.0` and the repository topics.
2. Cut a 30–60 second screen recording: screenshot → command → JSON → the same screenshot at 1280 px.
3. Post once per community, rewritten for each, not copy-pasted:
   - r/computervision, r/LocalLLaMA — "how much of a screenshot is dead space";
   - browser-agent / Playwright / browser-use discussions — coordinate caveat included;
   - Show HN — the measurement, not the marketing;
   - one Chinese note (Zhihu/WeChat), one Russian note (Habr/Telegram).
4. Ask 10 people who run vision agents for one real screenshot they would let you measure (or a synthetic
   stand-in with the same shape). Turn the best into `examples/`.
5. Open three good first issues: `--target-bytes`, AVIF output, a Playwright helper that rescales coordinates.

## What not to do

- Do not promise "50–80% cheaper" without a before/after from the reader's own file.
- Do not claim the model's answer stays identical; say what you tested.
- Do not buy stars, bots or fake testimonials.
- Do not call this a the engine project proof; it is a studio utility.
- Do not publish customer screenshots, invoices or faces without written permission.

## Success check after 30 days

- 10+ people ran it on their own image.
- 3 issues or PRs from outside the studio.
- 1 message that says "this cut my agent's bill" **with a number attached**.
- Stars are a bonus, not the goal.

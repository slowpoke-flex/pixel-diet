---
name: pixel-diet
description: Spend tokens on the answer, not on the pixels. Shrink screenshots, documents, sprites and camera frames with presets before sending them to a vision model, and compare images or masks with numbers instead of full-resolution pictures. Use when an agent looks at images, pays per image token, or has to decide whether two pictures differ.
---

# pixel-diet: spend tokens on the answer, not on the pixels

Two habits for any agent that works with images:

1. **Shrink the input** before a vision model pays for it.
2. **Measure the output** with numbers before a human or a model looks at pixels.

Origin: Mind Space Studio's render-inspection practice (2026-10-21), extended for vision pipelines.

## Rule zero

A visual claim needs a metric, a sample size and the command that produced it. One attractive output is not
evidence. One ugly output is not a failure. Report `n`, the slice, the metric and the threshold.

## Part 1 — shrink the input

### When to shrink

- A screenshot for a browser agent: `ui-agent` (crop solid borders, cap 1280 px, WebP q80).
- A receipt, invoice or scan: `ocr-document` (grayscale, autocontrast, cap 1024 px).
- A sprite or icon sheet: `game-sprite` (alpha bounding-box crop, lossless WebP).
- A camera frame on a weak link: `edge-fast` (cap 768 px, WebP q65).

### When not to shrink

- The task needs exact pixel coordinates and you will not rescale the answer back.
- The evidence must stay bit-exact (legal, medical, forensic, archival).
- The image is already small (under ~200 k pixels): cropping and re-encoding buys little.
- Fine text under ~8 px is the whole point of the task; raise `--max-dimension` instead of using a preset.

### Commands

```bash
pixel-diet shrink shot.png -o slim.webp --preset ui-agent
pixel-diet shrink ./inbox -o ./clean --preset ocr-document --json report.json
cat shot.png | pixel-diet shrink - -o - --preset ui-agent > slim.webp
```

Python, no disk I/O:

```python
from pixel_diet import optimize_bytes, optimize_for_llm

clean = optimize_bytes(raw_bytes, preset="ocr-document", max_dimension=1024)
uri = optimize_for_llm("shot.png", preset="ui-agent")   # data: URI for an image block
```

### Rules after shrinking

- **Coordinates:** map them back with `x * source_width / width` and `y * source_height / height`.
  Never click a raw coordinate read from a shrunk image.
- **Report the ratio**, not just "optimized": `1920x1080 -> 1280x720, 2.25x fewer image tokens`.
- **Verify on the real task**, not on the picture: run the task on the full-size and the shrunk image and
  compare the answers or the metrics. If it breaks, the preset is wrong for that task — say so.

## Part 2 — measure the output

### Order of tools (stop at the first that answers)

1. **Exact hash or metric, zero image tokens.** Identical bytes, PSNR, MAE, IoU, Dice, mAP, AbsRel, EPE. If the
   number answers the question, do not open the image.
2. **One-line verdict, then the region report.** `pixel-diet diff A.png B.png --brief --json report.json` prints
   a ~50-token line (PASS/FAIL, PSNR, SSIM, changed %, top regions) and writes the full report — MAE, max error and
   every connected region above threshold (line / blob / speck, box, peak) — to read only if the line is not enough.
3. **Slices, not averages.** Per class, per depth band, per resolution, per lighting condition.
4. **Diagnostic views instead of beauty renders.** Masks, error heatmaps, boundary maps, depth normals.
5. **Only then pixels.** The default contact sheet (`--sheet`, 768 px wide) costs ~260 image tokens; a full
   1280×720 frame costs ~1,200. One sheet per state change, not one per step.

### Metrics by task

| Task | Primary | Secondary | Watch for |
|---|---|---|---|
| Image / render | PSNR, SSIM, MAE | FLIP if installed, changed % | brightness/contrast shifts, one-pixel seams |
| Segmentation | IoU, Dice | boundary F, per-class IoU | class imbalance, small objects, null class |
| Detection | mAP@IoU, precision/recall | AP per class/size | NMS, duplicate boxes, calibration |
| Depth | AbsRel, RMSE | δ1, δ2, δ3 | scale/shift ambiguity, invalid pixels |
| Optical flow | EPE | outlier %, flow color map | occlusion, large motion |
| Keypoints | PCK, NME | per-joint error | missing joints, threshold choice |
| Generation | FID/KID or task metric | diversity, prompt adherence | sample size, preprocessing |

Never compare metrics computed with different preprocessing. State resize, color space, crop and normalization.

### Commands

```bash
python -m pixel_diet diff a.png b.png --json report.json --sheet sheet.png
python -m pixel_diet mask pred.png gt.png --classes 0,1,2 --json mask.json
python -m pixel_diet depth pred.png gt.png --scale 1.0 --json depth.json
```

All commands exit non-zero when a threshold fails (`--min-psnr`, `--min-iou`, `--max-absrel`). Use them in CI.

### Agent workflow

1. Fix the seed, the dataset slice and the preprocessing; write them in the report.
2. Run the metric first; if it passes, do one spot check with a contact sheet.
3. If it fails, classify the error: global shift, local blob, edge/line, speck, missing object. Open only the
   regions the tool names.
4. Attach `report.json` and `sheet.png`; never paste a full-resolution image into a report.
5. State what was **not** tested: other classes, other devices, other resolutions.

## Guardrails

- Do not cherry-pick the best sample. Report the slice and `n`.
- Do not use a metric your preprocessing invalidates (e.g., PSNR after a different tone map).
- Do not call a visual difference a bug until the diff localizes it.
- Do not call a metric a product win until it maps to a user-visible threshold.
- Do not quote a token saving without the formula and the before/after sizes.
- Keep private data out of public reports; crop or synthesize examples.

## Integration

- Claude Code: copy this folder to `~/.claude/skills/pixel-diet/`.
- Codex / OpenCode: add the `SKILL.md` body to `AGENTS.md` or reference it from a card.
- Cursor: copy the short rule from `docs/integrations/cursor.md` to `.cursor/rules/pixel-diet.mdc`.
- Any agent: run the CLI and read JSON; no framework plugin is required.
- GitHub Actions: see `docs/integrations/github-actions.md`.

## What this skill is not

It is not a model, a dataset or a benchmark leaderboard. It does not replace task-specific evaluation, human
review for subjective quality, or a held-out test set. It makes the first pass cheap and honest.

Mind Space Studio · MIT · https://github.com/slowpoke-flex/pixel-diet

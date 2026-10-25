---
name: vision-eval
description: Evaluate computer-vision and image outputs with numbers first and pixels last. Use before eyeballing model outputs, renders or screenshots: compare images, segmentation masks, depth maps, boxes and keypoints with metrics, diffs and small contact sheets instead of full-resolution pictures.
---

# Vision evaluation: numbers first, pixels last

A skill for agents that review computer-vision work. It applies to image generation, super-resolution,
segmentation, detection, depth, optical flow, keypoints and screenshot/render regression. It is model- and
framework-agnostic: the inputs are images, arrays and standard annotation formats.

Origin: Mind Space Studio's render-inspection practice (2026-10-21) generalized for CV.

## Rule zero

A visual claim needs a metric, a sample size and the command that produced it. One attractive output is not
evidence. One ugly output is not a failure. Report `n`, the slice, the metric and the threshold.

## Order of tools (stop at the first that answers)

1. **Exact hash or metric, zero image tokens.** Identical bytes, PSNR, MAE, IoU, Dice, mAP, AbsRel, EPE. If the
   number answers the question, do not open the image.
2. **Text diff and region report.** `vision-eval diff A.png B.png --json report.json` prints PSNR, SSIM, MAE,
   changed %, max error and the connected regions above threshold (line / blob / speck, box, peak).
3. **Slices, not averages.** Per class, per depth band, per resolution, per lighting condition. A global mean hides
   the failure that matters.
4. **Diagnostic views instead of beauty renders.** Masks, error heatmaps, boundary maps, depth normals, false-color
   flow. The raw output is data; the pretty render is marketing.
5. **Only then pixels.** A contact sheet of 32×32 crops (`--sheet`) costs ~400 image tokens for six regions; a full
   1280×720 frame costs ~1,200. One sheet per state change, not one per step.

## Metrics by task

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

## Commands

```bash
# image / render diff: JSON + optional contact sheet
python -m vision_eval diff a.png b.png --json report.json --sheet sheet.png

# binary or multi-class masks: IoU/Dice per class
python -m vision_eval mask pred.png gt.png --classes 0,1,2 --json mask.json

# depth: AbsRel/RMSE/delta, optional valid mask
python -m vision_eval depth pred.png gt.png --scale 1.0 --json depth.json
```

All commands exit non-zero when a threshold fails (`--min-psnr`, `--min-iou`, `--max-absrel`). Use them in CI.

## Agent workflow

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
- Keep private data out of public reports; crop or synthesize examples.

## Integration

- Claude Code: copy this folder to `~/.claude/skills/vision-eval/`.
- Codex / OpenCode: add the `SKILL.md` body to `AGENTS.md` or reference it from a card.
- Cursor: copy the short rule from `docs/integrations/cursor.md` to `.cursor/rules/vision-eval.mdc`.
- Any agent: run the CLI and read JSON; no framework plugin is required.
- GitHub Actions: see `docs/integrations/github-actions.md`.

## What this skill is not

It is not a model, a dataset or a benchmark leaderboard. It does not replace task-specific evaluation, human
review for subjective quality, or a held-out test set. It makes the first pass cheap and honest.

Mind Space Studio · MIT · https://github.com/slowpoke-flex/vision-eval

---
description: Numbers-first computer-vision evaluation with vision-eval
globs: ["**/*.png", "**/*.jpg", "**/*.npy", "**/*.py"]
alwaysApply: false
---
# Vision review
Before opening an image, run `vision-eval diff A B --json report.json --sheet sheet.png`.
Read the JSON first; open only the named regions. Report n, slice, metric and threshold.
Never paste full-resolution frames into a report; attach JSON and the contact sheet.

# Claude Code

1. Copy this repository to `~/.claude/skills/vision-eval/` (or symlink it).
2. Install the CLI once: `python -m pip install -e .` from the repository root.
3. Ask Claude to use the skill before opening images:

```text
Use vision-eval. Run `vision-eval diff A B --json report.json --sheet sheet.png`,
read report.json, and only open the named regions. Do not paste full frames.
```

The skill is model-agnostic; the CLI does the measuring.

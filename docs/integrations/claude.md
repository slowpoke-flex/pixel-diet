# Claude Code

1. Copy this repository to `~/.claude/skills/pixel-diet/` (or symlink it).
2. Install the CLI once: `python -m pip install -e .` from the repository root.
3. Ask Claude to use the skill before opening images:

```text
Use pixel-diet. Run `pixel-diet diff A B --brief --json report.json --sheet sheet.png`,
read report.json, and only open the named regions. Do not paste full frames.
```

The skill is model-agnostic; the CLI does the measuring.

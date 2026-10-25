# OpenCode

Add the skill to `AGENTS.md` or to a card:

```markdown
Use `pixel-diet` before opening any image. Run the CLI, read JSON, open only the
regions named by the report. Report n, slice, metric and threshold.
```

```bash
opencode run --model <provider>/<model> "Run pixel-diet on examples/ and summarize the report."
```

The repository is a normal Python package; `python -m pip install -e .` is the only setup.

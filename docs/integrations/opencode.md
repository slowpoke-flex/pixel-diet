# OpenCode

Add the skill to `AGENTS.md` or to a card:

```markdown
Use `vision-eval` before opening any image. Run the CLI, read JSON, open only the
regions named by the report. Report n, slice, metric and threshold.
```

```bash
opencode run --model <provider>/<model> "Run vision-eval on examples/ and summarize the report."
```

The repository is a normal Python package; `python -m pip install -e .` is the only setup.

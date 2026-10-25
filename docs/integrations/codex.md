# Codex / OpenAI Codex CLI

Add the `SKILL.md` body to the project `AGENTS.md`, or keep it as a referenced file:

```markdown
## Vision review
Before looking at an image, run `pixel-diet diff A B --brief --json report.json`.
Read the JSON first; open only the regions it names. State n, slice and threshold.
```

Run Codex from the repository root:

```bash
codex exec -s workspace-write "Run pixel-diet diff examples/a.png examples/b.png and summarize the JSON."
```

Codex does not need a plugin: the CLI and a JSON report are enough.

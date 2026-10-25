# MCP

Expose the CLI as a tool in any MCP server. The schema is intentionally small:

```json
{
  "name": "vision_eval_diff",
  "description": "Compare two images, return JSON metrics and optional sheet path.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "a": {"type": "string"},
      "b": {"type": "string"},
      "min_psnr": {"type": "number"}
    },
    "required": ["a", "b"]
  }
}
```

Implementation: run `vision-eval diff A B --json <tmp>/report.json`, read the JSON, return it as text.
Do not return the image bytes; return the report path and metrics. Keep the server local-only unless you add
authentication.

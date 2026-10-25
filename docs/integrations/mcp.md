# MCP

Expose the CLI as a tool in any MCP server. The schema is intentionally small:

```json
{
  "name": "pixel_diet_diff",
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

Implementation: run `pixel-diet diff A B --json <tmp>/report.json`, read the JSON, return it as text.
Do not return the image bytes; return the report path and metrics. Keep the server local-only unless you add
authentication.

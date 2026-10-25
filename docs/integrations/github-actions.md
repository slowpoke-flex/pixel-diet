# GitHub Actions

```yaml
name: vision-eval
on: [pull_request]
jobs:
  images:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: python -m pip install -e .
      - run: python examples/make_examples.py
      - run: vision-eval diff examples/a.png examples/b.png --json report.json --sheet sheet.png --min-psnr 20
      - uses: actions/upload-artifact@v4
        if: always()
        with: {name: vision-report, path: "report.json\nsheet.png"}
```

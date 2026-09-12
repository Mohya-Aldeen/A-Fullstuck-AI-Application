# Data

Local data artifacts for development live here.

- `downloads/` — raw HTML from SEC EDGAR, grouped by year + `manifest.json`
- `markdown/` — Docling Markdown output with the **same year layout** + `manifest.json`
- Both folders are gitignored (large generated artifacts)

## 1. Download sample corpus

```bash
uv run data/download.py
```

Produces `data/downloads/<year>/…html` and `data/downloads/manifest.json` (25 ten-Ks: 5 tickers × 5 years).

## 2. Convert HTML → Markdown (Docling)

```bash
uv run data/convert_to_markdown.py
```

Reads `downloads/manifest.json` (or scans `downloads/**/*.html` if no manifest), writes `markdown/<year>/….md` and `markdown/manifest.json`.

Options at the top of `convert_to_markdown.py`: `CLEAR_OUTPUT_DIR`, `SKIP_EXISTING`.

Docling docs: https://docling-project.github.io/docling/

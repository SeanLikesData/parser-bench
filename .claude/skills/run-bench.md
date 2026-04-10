---
description: Run the parser benchmark suite
---

# Running Parser Bench

## Commands

Run from the project root (`/Users/s/1w/1-dev/1-now/parser-bench`).

```sh
# Run everything (standard + hard suites, all parsers)
.venv/bin/python -m parser_bench

# Run a specific suite
.venv/bin/python -m parser_bench --suite standard
.venv/bin/python -m parser_bench --suite hard

# Run specific parsers only (case-insensitive)
.venv/bin/python -m parser_bench --parsers pymupdf,pypdf

# Customize timing
.venv/bin/python -m parser_bench --runs 10 --warmup 2

# Skip dashboard generation (JSON only)
.venv/bin/python -m parser_bench --no-dashboard

# Custom directories
.venv/bin/python -m parser_bench --docs-dir ./my-pdfs --output-dir ./my-results
```

## Defaults

- `--suite all` -- runs both standard and hard suites
- `--runs 5` -- 5 timed runs per parser per document
- `--warmup 1` -- 1 warmup run before timing begins
- `--docs-dir docs` -- expects `docs/standard/` and `docs/hard/` subdirectories
- `--output-dir results` -- writes `results.json`, `results_hard.json`, `dashboard.html`, `dashboard_hard.html`

## Output

- `results/results.json` -- standard suite results with environment metadata
- `results/results_hard.json` -- hard suite results
- `results/dashboard.html` -- interactive standard benchmark dashboard (Chart.js)
- `results/dashboard_hard.html` -- interactive hard benchmark dashboard

## Available Parsers

Check the current registry:

```sh
.venv/bin/python -c "from parser_bench.parsers import list_parsers; print(list_parsers())"
```

Current parsers: PyMuPDF, pdfplumber, pypdf, LiteParse.

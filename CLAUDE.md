# Parser Bench

PDF parser benchmarking suite comparing PyMuPDF, pdfplumber, pypdf, and LiteParse.

## Project Structure

```
parser-bench/
├── parser_bench/           # Python package
│   ├── __main__.py         # CLI entry point
│   ├── parsers.py          # Parser registry (single source of truth)
│   ├── runner.py           # Timing harness, stats, environment capture
│   ├── quality.py          # Quality test functions (reading order, numeric, etc.)
│   ├── tests.py            # Test definitions for standard and hard suites
│   └── dashboard.py        # HTML dashboard generation
├── docs/
│   ├── standard/           # Standard test PDFs (5 docs)
│   └── hard/               # Hard test PDFs (6 docs)
├── results/                # Output: JSON results + HTML dashboards
└── pyproject.toml
```

## Running

```sh
.venv/bin/python -m parser_bench              # all suites, all parsers
.venv/bin/python -m parser_bench --suite standard
.venv/bin/python -m parser_bench --suite hard
.venv/bin/python -m parser_bench --parsers pymupdf,pypdf --runs 10 --warmup 2
```

Output goes to `results/` by default (JSON + HTML dashboards).

## Key Design Decisions

- **Parser registry pattern**: parsers are registered via `@register()` decorator in `parsers.py` with metadata (`pure_python`, `multi_format`). This is the single source of truth -- adding a parser here makes it available everywhere.
- **PyMuPDF is NOT pure Python** -- it wraps MuPDF via C extensions. This is correctly reflected in the registry.
- **Standard suite** tests content accuracy (expected phrase matching), speed, bbox support, and table extraction across `docs/standard/` PDFs.
- **Hard suite** tests specific quality dimensions (reading order, column separation, watermark filtering, numeric extraction, table row integrity) across `docs/hard/` PDFs.
- **All parsers return the same page dict format**: `{text, bboxes, has_bbox, tables, page}`.

## Adding New Parsers or Documents

See `.claude/skills/` for step-by-step instructions:
- `add-parser.md` -- how to add a new parser
- `add-document.md` -- how to add a new test document
- `run-bench.md` -- how to run benchmarks

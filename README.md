# parser-bench

Benchmarking suite for Python PDF parsers. Compares speed, accuracy, and feature support across real-world documents.

## Parsers tested

| Parser | Speed | Pure Python | Bounding Boxes | Tables | Multi-Format |
|--------|-------|-------------|----------------|--------|--------------|
| **pypdf** | ~22ms | Yes | No | No | No |
| **PyMuPDF** | ~45ms | No (C/MuPDF) | Yes | No | No |
| **pdfplumber** | ~215ms | Yes | Yes | Yes | No |
| **LiteParse** | ~2.4s | No (API) | No | No | Yes |

## Test documents

**Standard suite** (5 docs): IRS W-9 form, financial report, two-column academic paper, employee database with pivot tables, board meeting minutes.

**Hard suite** (6 docs): watermarked financial projections, clinical trial tables, tax compliance with formulas, two-column insurance policy, Fed financial stability report, Census Bureau operational plan.

## Usage

```sh
python -m venv .venv
.venv/bin/pip install -e .

# Run all benchmarks
.venv/bin/python -m parser_bench

# Run a specific suite
.venv/bin/python -m parser_bench --suite standard
.venv/bin/python -m parser_bench --suite hard

# Select parsers, customize runs
.venv/bin/python -m parser_bench --parsers pymupdf,pypdf --runs 10 --warmup 2

# JSON only, skip dashboards
.venv/bin/python -m parser_bench --no-dashboard
```

Results and interactive dashboards (Chart.js) are written to `results/`.

## Project structure

```
parser_bench/
├── __main__.py     CLI entry point
├── parsers.py      Parser registry (@register decorator)
├── runner.py       Timing harness with warmup, std dev, environment capture
├── quality.py      Quality tests (reading order, numeric, table, watermark, columns)
├── tests.py        Test definitions for both suites
└── dashboard.py    HTML dashboard generation
docs/
├── standard/       Standard test PDFs
└── hard/           Hard test PDFs
results/            Output (JSON + HTML dashboards)
```

## Adding a parser

Add a function to `parser_bench/parsers.py` with the `@register` decorator:

```python
@register("MyParser", pure_python=True, multi_format=False)
def parse_myparser(path, *, pages_limit=None):
    import myparser_lib
    pages = []
    for i, page in enumerate(parsed_pages):
        if pages_limit and i >= pages_limit:
            break
        pages.append({
            "text": page.get_text(),
            "bboxes": [],
            "has_bbox": False,
            "tables": [],
            "page": i,
        })
    return pages
```

Add the dependency to `pyproject.toml` and it's ready to benchmark.

## Adding a test document

Drop a PDF into `docs/standard/` or `docs/hard/`, then add a test definition to `parser_bench/tests.py`. Standard tests check content accuracy via expected phrases. Hard tests check specific quality dimensions: reading order, column separation, numeric extraction, table row integrity, and watermark filtering.

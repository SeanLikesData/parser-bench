# parser-bench

Benchmarking suite for Python PDF parsers, focused on **extraction quality** -- not just speed. Tests content accuracy, reading order, table fidelity, column handling, watermark separation, and numeric precision across 11 real-world documents.

## Parsers tested

- **PyMuPDF** (fitz) -- C-backed via MuPDF, span-level bounding boxes, broad format support
- **pdfplumber** -- pure Python, best-in-class table extraction, char-level coordinates
- **pypdf** -- pure Python, lightweight, no native dependencies
- **LiteParse** -- API-based, multi-format (PDF, DOCX, PPTX, XLSX, images), auto-OCR

## Format support

| Format | PyMuPDF | pdfplumber | pypdf | LiteParse |
|--------|---------|------------|-------|-----------|
| PDF | Y | Y | Y | Y |
| DOCX / DOC / ODT / RTF | - | - | - | Y |
| PPTX / PPT / ODP | - | - | - | Y |
| XLSX / XLS / ODS / CSV | - | - | - | Y |
| Images (PNG, JPG, TIFF) | Y | - | - | Y |
| EPUB / MOBI / FB2 | Y | - | - | - |
| XPS / SVG / CBZ | Y | - | - | - |
| Password-protected PDFs | Y | Y | Y | Y |

## Extraction capabilities

| Capability | PyMuPDF | pdfplumber | pypdf | LiteParse |
|------------|---------|------------|-------|-----------|
| Plain text | Y | Y | Y | Y |
| Bounding boxes | Y (span) | Y (char) | - | Y (line) |
| Table extraction | ~ | **Y (best)** | - | Y |
| Embedded images | Y | Y | Y | - |
| OCR (scanned docs) | Y | - | - | **Y (auto)** |
| Form fields / AcroForms | ~ | Y | **Y (best)** | - |
| Annotations | Y | Y | Y | - |
| Metadata | Y | Y | Y | - |
| Bookmarks / TOC | Y | - | - | - |
| Font info (name, size, color) | Y | - | - | - |
| PDF manipulation (merge, split) | Y | - | **Y (best)** | - |

## Quality results

### Content accuracy (standard suite)

Percentage of expected phrases found in extracted text across 5 standard documents:

| Document | PyMuPDF | pdfplumber | pypdf | LiteParse |
|----------|---------|------------|-------|-----------|
| IRS W-9 Form | 100% | 100% | 100% | 100% |
| Financial Report | 83% | 100% | 100% | 83% |
| Multi-Column Paper | 83% | 83% | 83% | 83% |
| Employee Database | 100% | 100% | 100% | 100% |
| Board Minutes (4pg) | 100% | 100% | 100% | 100% |
| **Average** | **93%** | **97%** | **97%** | **93%** |

### Hard quality tests

Targeted tests on 6 challenging documents. Each cell shows pass rate for that specific quality dimension.

**Watermarked Financial Projections**

| Test | PyMuPDF | pdfplumber | pypdf | LiteParse |
|------|---------|------------|-------|-----------|
| Watermark vs content separation | 100% | 67% (interleaved) | 100% | 100% (interleaved) |
| Financial numbers intact | 100% | 92% | 100% | 100% |
| Sensitivity table rows | 100% | 100% | 100% | 67% |
| Reading order | 100% | 100% | 100% | 100% |

**Clinical Trial Table**

| Test | PyMuPDF | pdfplumber | pypdf | LiteParse |
|------|---------|------------|-------|-----------|
| Table row integrity | **0%** | 100% | 100% | 100% |
| Statistical values present | 100% | 100% | 100% | 100% |
| Section order | 100% | 100% | 100% | 100% |

PyMuPDF splits table rows across lines, breaking row integrity. pdfplumber, pypdf, and LiteParse keep row values together.

**Tax Compliance Report**

| Test | PyMuPDF | pdfplumber | pypdf | LiteParse |
|------|---------|------------|-------|-----------|
| Treaty table rows | 100% | 100% | 100% | 100% |
| Formulas & calculations | 100% | 100% | 100% | 100% |
| Legal citations | 100% | 100% | 100% | 100% |

**Two-Column Insurance Policy**

| Test | PyMuPDF | pdfplumber | pypdf | LiteParse |
|------|---------|------------|-------|-----------|
| Column reading order | 100% (separate) | **40% (interleaved)** | 100% (separate) | **40% (interleaved)** |
| Defined terms present | 86% | 86% | 86% | 86% |
| Footer data | 100% | 100% | 100% | 100% |

pdfplumber and LiteParse read across columns instead of down them, mixing left and right column text.

**Real government documents** (Fed report + Census plan): all parsers extract key content, but all struggle with reading order on the Census document.

### Key takeaways

- **pypdf** has the best overall quality -- highest content accuracy and correct column/reading order handling, with no major weaknesses
- **PyMuPDF** handles columns and watermarks well, but breaks table row structure
- **pdfplumber** excels at table extraction but fails on two-column layouts and watermark separation
- **LiteParse** matches pypdf on most tests but fails on column layouts and some table structures

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

---
description: Add a new test document to the benchmark suite
---

# Adding a New Test Document

Documents go in `docs/standard/` or `docs/hard/` depending on the suite. Test definitions go in `parser_bench/tests.py`.

## Adding to the Standard Suite

The standard suite measures speed, content accuracy, bbox support, and table extraction.

### 1. Place the PDF

Copy the PDF into `docs/standard/`:

```sh
cp my_new_document.pdf docs/standard/
```

### 2. Add a test definition

Add an entry to `STANDARD_TESTS` in `parser_bench/tests.py`:

```python
STANDARD_TESTS = {
    ...
    "my_new_document.pdf": {
        "label": "My New Document",                    # Short display name
        "description": "What makes this document interesting",  # One-line description
        "expected": [
            # Phrases that should appear in correctly extracted text.
            # Use 8-15 phrases that cover different parts of the document.
            # Include tricky content: numbers, special chars, headers, footers.
            "First expected phrase",
            "Second expected phrase",
            "$1,234.56",
            "Section Header",
        ],
    },
}
```

### 3. Run it

```sh
.venv/bin/python -m parser_bench --suite standard
```

## Adding to the Hard Suite

The hard suite runs targeted quality tests. Use this for documents that stress-test specific parser capabilities.

### 1. Place the PDF

```sh
cp my_hard_document.pdf docs/hard/
```

### 2. Add a test definition

Add an entry to `HARD_TESTS` in `parser_bench/tests.py`:

```python
HARD_TESTS = [
    ...
    {
        "file": "my_hard_document.pdf",
        "label": "My Hard Document",
        "pages_limit": None,           # or an int to limit pages parsed (useful for large PDFs)
        "tests": [
            # Add one or more quality tests (see test types below)
        ],
    },
]
```

### 3. Choose test types

Available test types (defined in `parser_bench/quality.py`):

**`numeric`** -- Check if specific values appear verbatim:
```python
{
    "name": "Financial Numbers Intact",
    "type": "numeric",
    "expected": ["$42,150", "22.9%", "($16,860)"],
}
```

**`table`** -- Check if table row values appear on the same line:
```python
{
    "name": "Table Row Integrity",
    "type": "table",
    "rows": [
        ["Row Label", "Value1", "Value2"],   # all must appear on one line
        ["Another Row", "Val3", "Val4"],
    ],
}
```

**`order`** -- Check if phrases appear in the expected sequential order:
```python
{
    "name": "Reading Order",
    "type": "order",
    "phrases": ["Introduction", "Methods", "Results", "Conclusion"],
}
```

**`columns`** -- Check if two-column text is read column-by-column (not across):
```python
{
    "name": "Column Reading Order",
    "type": "columns",
    "left": ["phrase from left column", "another left phrase"],
    "right": ["phrase from right column", "another right phrase"],
}
```

**`watermark`** -- Check if watermark text is separated from content:
```python
{
    "name": "Watermark Separation",
    "type": "watermark",
    "content_phrases": ["Revenue", "EBITDA", "Net Income"],
    "watermark_phrases": ["DRAFT", "CONFIDENTIAL"],
}
```

### 4. Run it

```sh
.venv/bin/python -m parser_bench --suite hard
```

## Tips

- Pick expected phrases from different parts of the document (beginning, middle, end)
- Include content that parsers commonly struggle with: dollar amounts with parenthetical negatives `($1,234)`, percentages, special characters, footnote references
- For large PDFs (>1MB), set `pages_limit` to keep benchmarks fast
- A good standard test has 8-15 expected phrases; a good hard test has 2-4 targeted quality checks

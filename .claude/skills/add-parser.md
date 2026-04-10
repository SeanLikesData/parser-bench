---
description: Add a new PDF parser to the benchmark suite
---

# Adding a New Parser

All parsers live in `parser_bench/parsers.py`. Follow these steps:

## 1. Add the parser function

Add a new function in `parser_bench/parsers.py` with the `@register()` decorator:

```python
@register("MyParser", pure_python=True, multi_format=False)
def parse_myparser(path, *, pages_limit=None):
    import myparser_lib
    # ... parse the PDF ...
    pages = []
    for i, page in enumerate(parsed_pages):
        if pages_limit and i >= pages_limit:
            break
        pages.append({
            "text": page.get_text(),       # required: extracted text as str
            "bboxes": [],                   # list of {"text": str, "bbox": [x0, y0, x1, y1]}
            "has_bbox": False,              # True if bboxes are populated
            "tables": [],                   # list of extracted tables (list of lists)
            "page": i,                      # page index
        })
    return pages
```

## 2. Register metadata

The `@register()` decorator takes:
- `name` (str): display name used in CLI, dashboards, and results
- `pure_python` (bool): True if the library has no native/C dependencies
- `multi_format` (bool): True if the library supports formats beyond PDF

## 3. Add the dependency

Add the library to `pyproject.toml` under `[project.dependencies]`, then install:

```sh
# Edit pyproject.toml to add the dependency, then:
.venv/bin/pip install -e .
```

## 4. Add a color (optional)

If you want a custom color in dashboards, add an entry to the `COLORS` dict in `parser_bench/dashboard.py`:

```python
COLORS = {
    ...
    "MyParser": "#8b5cf6",  # purple, or any hex color
}
```

If omitted, the dashboard uses a gray fallback.

## 5. Test it

```sh
.venv/bin/python -m parser_bench --parsers myparser --suite standard --runs 1
```

## Contract

Every parser function MUST:
- Accept `(path, *, pages_limit=None)` as its signature
- Return a list of dicts, one per page, with keys: `text`, `bboxes`, `has_bbox`, `tables`, `page`
- Import its library inside the function body (lazy import), not at module level
- Handle `pages_limit` by stopping iteration when the limit is reached

That's it. The runner, dashboards, and CLI will pick up the new parser automatically from the registry.

"""
Unified parser implementations.

Each parser function takes a PDF path and optional pages_limit,
and returns a list of page dicts with keys:
  - text: str
  - bboxes: list[dict] with text + bbox keys
  - has_bbox: bool
  - tables: list (pdfplumber only)
  - page: int (page index)
"""

import json


PARSER_REGISTRY = {}


def register(name, *, pure_python=False, multi_format=False):
    """Decorator to register a parser with metadata."""
    def decorator(fn):
        PARSER_REGISTRY[name] = {
            "fn": fn,
            "pure_python": pure_python,
            "multi_format": multi_format,
        }
        return fn
    return decorator


@register("PyMuPDF", pure_python=False, multi_format=False)
def parse_pymupdf(path, *, pages_limit=None):
    import fitz
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc):
        if pages_limit and i >= pages_limit:
            break
        blocks = page.get_text("dict")["blocks"]
        bbox_items = []
        for b in blocks:
            if "lines" in b:
                for line in b["lines"]:
                    for span in line["spans"]:
                        bbox_items.append({
                            "text": span["text"],
                            "bbox": list(span["bbox"]),
                        })
        pages.append({
            "text": page.get_text(),
            "bboxes": bbox_items,
            "has_bbox": True,
            "tables": [],
            "page": i,
        })
    doc.close()
    return pages


@register("pdfplumber", pure_python=True, multi_format=False)
def parse_pdfplumber(path, *, pages_limit=None):
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages_limit and i >= pages_limit:
                break
            words = page.extract_words()
            tables = page.extract_tables() or []
            bbox_items = [
                {"text": w["text"], "bbox": [w["x0"], w["top"], w["x1"], w["bottom"]]}
                for w in words
            ]
            pages.append({
                "text": page.extract_text() or "",
                "bboxes": bbox_items,
                "has_bbox": True,
                "tables": tables,
                "page": i,
            })
    return pages


@register("pypdf", pure_python=True, multi_format=False)
def parse_pypdf(path, *, pages_limit=None):
    from pypdf import PdfReader
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        if pages_limit and i >= pages_limit:
            break
        pages.append({
            "text": page.extract_text() or "",
            "bboxes": [],
            "has_bbox": False,
            "tables": [],
            "page": i,
        })
    return pages


@register("LiteParse", pure_python=False, multi_format=True)
def parse_liteparse(path, *, pages_limit=None):
    from liteparse import LiteParse
    parser = LiteParse()

    # Try JSON mode first for bbox data
    try:
        kwargs = {}
        if pages_limit:
            kwargs["target_pages"] = f"0-{pages_limit - 1}"
        result = parser.parse(path, format="json", **kwargs)
        pages = []
        for i, page in enumerate(result.pages):
            data = json.loads(page.text) if isinstance(page.text, str) else page.text
            bbox_items = []
            plain_lines = []
            if isinstance(data, dict) and "blocks" in data:
                for block in data["blocks"]:
                    if isinstance(block, dict):
                        text = block.get("text", "")
                        bbox = block.get("bbox")
                        if text:
                            plain_lines.append(text)
                        if bbox:
                            bbox_items.append({"text": text, "bbox": bbox})
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        text = item.get("text", item.get("content", ""))
                        bbox = item.get("bbox", item.get("bounding_box"))
                        if text:
                            plain_lines.append(text)
                        if bbox:
                            bbox_items.append({"text": text, "bbox": bbox})
            else:
                plain_lines = [str(data)]

            pages.append({
                "text": "\n".join(plain_lines) if plain_lines else str(data),
                "bboxes": bbox_items,
                "has_bbox": len(bbox_items) > 0,
                "tables": [],
                "page": i,
            })
        return pages
    except Exception:
        pass

    # Fallback to plain text mode
    kwargs = {}
    if pages_limit:
        kwargs["target_pages"] = f"0-{pages_limit - 1}"
    result = parser.parse(path, **kwargs)
    pages = []
    for i, page in enumerate(result.pages):
        pages.append({
            "text": page.text,
            "bboxes": [],
            "has_bbox": False,
            "tables": [],
            "page": i,
        })
    return pages


def get_parser(name):
    """Get a parser function by name."""
    return PARSER_REGISTRY[name]["fn"]


def get_parser_meta(name):
    """Get parser metadata (pure_python, multi_format)."""
    entry = PARSER_REGISTRY[name]
    return {k: v for k, v in entry.items() if k != "fn"}


def list_parsers():
    """Return list of registered parser names."""
    return list(PARSER_REGISTRY.keys())

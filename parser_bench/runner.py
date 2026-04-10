"""
Benchmark runner with warmup, statistical reporting, and environment capture.
"""

import os
import platform
import statistics
import sys
import time


def capture_environment():
    """Capture system and library info for reproducibility."""
    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }

    # Library versions
    libs = {}
    try:
        import fitz
        libs["pymupdf"] = fitz.version[0]
    except Exception:
        pass
    try:
        import pdfplumber
        libs["pdfplumber"] = pdfplumber.__version__
    except Exception:
        pass
    try:
        import pypdf
        libs["pypdf"] = pypdf.__version__
    except Exception:
        pass
    try:
        import liteparse
        libs["liteparse"] = getattr(liteparse, "__version__", "unknown")
    except Exception:
        pass

    env["libraries"] = libs
    return env


def run_timed(parser_fn, pdf_path, *, runs=5, warmup=1, pages_limit=None):
    """Run a parser with warmup and return timing + result data.

    Returns dict with:
      - pages: list of page dicts from the last run
      - times: list of run durations in seconds (excluding warmup)
      - warmup_times: list of warmup durations
      - error: str if parser failed, None otherwise
      - stats: dict with avg_ms, std_ms, min_ms, median_ms, p95_ms
    """
    warmup_times = []
    times = []
    pages = None
    error = None

    # Warmup runs
    for _ in range(warmup):
        try:
            t0 = time.perf_counter()
            pages = parser_fn(pdf_path, pages_limit=pages_limit)
            elapsed = time.perf_counter() - t0
            warmup_times.append(elapsed)
        except Exception as e:
            return {
                "pages": None,
                "times": [],
                "warmup_times": [],
                "error": str(e),
                "stats": None,
            }

    # Timed runs
    for _ in range(runs):
        try:
            t0 = time.perf_counter()
            pages = parser_fn(pdf_path, pages_limit=pages_limit)
            elapsed = time.perf_counter() - t0
            times.append(elapsed)
        except Exception as e:
            error = str(e)
            break

    if error or not times:
        return {
            "pages": pages,
            "times": times,
            "warmup_times": warmup_times,
            "error": error,
            "stats": None,
        }

    times_ms = [t * 1000 for t in times]
    sorted_ms = sorted(times_ms)
    p95_idx = max(0, int(len(sorted_ms) * 0.95) - 1)

    stats = {
        "avg_ms": round(statistics.mean(times_ms), 2),
        "std_ms": round(statistics.stdev(times_ms), 2) if len(times_ms) > 1 else 0.0,
        "min_ms": round(min(times_ms), 2),
        "median_ms": round(statistics.median(times_ms), 2),
        "p95_ms": round(sorted_ms[p95_idx], 2),
        "runs": len(times),
        "warmup_runs": len(warmup_times),
    }

    return {
        "pages": pages,
        "times": [round(t * 1000, 2) for t in times],
        "warmup_times": [round(t * 1000, 2) for t in warmup_times],
        "error": None,
        "stats": stats,
    }


def text_quality_metrics(text):
    """Compute basic text quality metrics."""
    lines = text.strip().split("\n")
    words = text.split()
    return {
        "chars": len(text),
        "words": len(words),
        "lines": len(lines),
        "empty_lines": sum(1 for line in lines if not line.strip()),
        "avg_line_len": round(statistics.mean(len(line) for line in lines), 1) if lines else 0,
    }


def check_known_content(text, expected_phrases):
    """Check how many expected phrases appear in the extracted text."""
    found = sum(1 for phrase in expected_phrases if phrase.lower() in text.lower())
    return found, len(expected_phrases)


def find_pdfs(docs_dir):
    """Find all PDF files in the given directory."""
    if not os.path.isdir(docs_dir):
        return []
    return sorted(
        os.path.join(docs_dir, f)
        for f in os.listdir(docs_dir)
        if f.endswith(".pdf")
    )

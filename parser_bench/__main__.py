"""
CLI entry point for parser-bench.

Usage:
    python -m parser_bench                         # Run all suites
    python -m parser_bench --suite standard        # Standard suite only
    python -m parser_bench --suite hard            # Hard suite only
    python -m parser_bench --parsers pymupdf,pypdf # Select parsers
    python -m parser_bench --runs 10               # Custom run count
    python -m parser_bench --warmup 2              # Custom warmup count
    python -m parser_bench --docs-dir ./pdfs       # Custom docs root (expects standard/ and hard/ subdirs)
"""

import argparse
import json
import os
import sys
import time

from .parsers import get_parser, list_parsers
from .runner import (
    capture_environment,
    check_known_content,
    run_timed,
    text_quality_metrics,
)
from .quality import (
    test_column_separation,
    test_numeric_extraction,
    test_reading_order,
    test_table_structure,
    test_watermark_separation,
)
from .tests import HARD_TESTS, STANDARD_TESTS
from .dashboard import generate_hard_dashboard, generate_standard_dashboard


def run_standard_suite(parsers, docs_dir, *, runs, warmup):
    """Run the standard benchmark suite."""
    results = {}

    for pdf_file, test_info in STANDARD_TESTS.items():
        pdf_path = os.path.join(docs_dir, pdf_file)
        if not os.path.exists(pdf_path):
            print(f"  SKIP: {pdf_file} not found")
            continue

        file_size = os.path.getsize(pdf_path)
        print(f"\n{'=' * 60}")
        print(f"  {test_info['label']} ({pdf_file}, {file_size / 1024:.0f}KB)")
        print(f"{'=' * 60}")

        results[pdf_file] = {
            "label": test_info["label"],
            "description": test_info["description"],
            "file_size": file_size,
            "parsers": {},
        }

        for parser_name in parsers:
            parser_fn = get_parser(parser_name)
            result = run_timed(parser_fn, pdf_path, runs=runs, warmup=warmup)

            if result["error"]:
                results[pdf_file]["parsers"][parser_name] = {"error": result["error"]}
                print(f"  {parser_name}: ERROR - {result['error'][:80]}")
                continue

            pages = result["pages"]
            all_text = "\n".join(p["text"] for p in pages)
            metrics = text_quality_metrics(all_text)
            found, total = check_known_content(all_text, test_info["expected"])
            has_bbox = any(p["has_bbox"] for p in pages)
            total_bboxes = sum(len(p["bboxes"]) for p in pages)
            has_tables = any(p.get("tables") for p in pages)
            table_count = sum(len(p.get("tables", [])) for p in pages)

            stats = result["stats"]
            content_pct = round(found / total * 100, 1) if total else 0

            pr = {
                "stats": stats,
                "pages": len(pages),
                "metrics": metrics,
                "content_found": found,
                "content_total": total,
                "content_pct": content_pct,
                "has_bbox": has_bbox,
                "bbox_count": total_bboxes,
                "has_tables": has_tables,
                "table_count": table_count,
                "text_preview": all_text[:600],
            }
            results[pdf_file]["parsers"][parser_name] = pr

            std_str = f" +/-{stats['std_ms']:.0f}" if stats["std_ms"] > 0 else ""
            print(
                f"  {parser_name}: {stats['avg_ms']:.0f}ms{std_str} | "
                f"{metrics['words']} words | "
                f"content: {found}/{total} ({content_pct}%) | "
                f"bbox: {'Yes' if has_bbox else 'No'} ({total_bboxes})"
                + (f" | tables: {table_count}" if has_tables else "")
            )

    return results


def run_hard_suite(parsers, docs_dir):
    """Run the hard benchmark suite (quality-focused, single run)."""
    all_results = []

    for test_suite in HARD_TESTS:
        pdf = test_suite["file"]
        pdf_path = os.path.join(docs_dir, pdf)
        if not os.path.exists(pdf_path):
            print(f"  SKIP: {pdf}")
            continue

        fsize = os.path.getsize(pdf_path)
        plimit = test_suite.get("pages_limit")
        print(f"\n{'=' * 70}")
        print(f"  {test_suite['label']} ({pdf}, {fsize / 1024:.0f}KB"
              f"{f', first {plimit} pages' if plimit else ''})")
        print(f"{'=' * 70}")

        suite_result = {
            "file": pdf,
            "label": test_suite["label"],
            "file_size": fsize,
            "parsers": {},
        }

        for parser_name in parsers:
            parser_fn = get_parser(parser_name)
            t0 = time.perf_counter()
            try:
                pages = parser_fn(pdf_path, pages_limit=plimit)
                elapsed = time.perf_counter() - t0
            except Exception as e:
                suite_result["parsers"][parser_name] = {"error": str(e)[:120], "time_ms": 0}
                print(f"\n  {parser_name}: ERROR - {str(e)[:80]}")
                continue

            text = "\n".join(p["text"] for p in pages)
            parser_result = {
                "time_ms": round(elapsed * 1000, 1),
                "words": len(text.split()),
                "chars": len(text),
                "pages": len(pages),
                "tests": {},
                "text_preview": text[:600],
            }

            print(f"\n  {parser_name} ({elapsed * 1000:.0f}ms, {len(text.split()):,} words):")

            for test in test_suite["tests"]:
                tname = test["name"]

                if test["type"] == "watermark":
                    cf, ct, wf, interleaved = test_watermark_separation(
                        text, test["content_phrases"], test["watermark_phrases"]
                    )
                    score = f"{cf}/{ct} content"
                    if wf > 0:
                        score += f", {wf} watermark lines found ({interleaved} interleaved)"
                    else:
                        score += ", watermarks filtered"
                    parser_result["tests"][tname] = {
                        "content_found": cf, "content_total": ct,
                        "watermark_found": wf, "interleaved": interleaved,
                        "score_pct": round(cf / ct * 100, 1) if ct else 0,
                        "penalty": interleaved,
                    }

                elif test["type"] == "numeric":
                    found, total, missing = test_numeric_extraction(text, test["expected"])
                    pct = round(found / total * 100, 1) if total else 0
                    score = f"{found}/{total} ({pct}%)"
                    if missing:
                        score += f"  missing: {missing[:3]}"
                    parser_result["tests"][tname] = {
                        "found": found, "total": total, "pct": pct, "missing": missing[:5],
                    }

                elif test["type"] == "table":
                    found, total, missing = test_table_structure(text, test["rows"])
                    pct = round(found / total * 100, 1) if total else 0
                    score = f"{found}/{total} rows intact ({pct}%)"
                    parser_result["tests"][tname] = {
                        "found": found, "total": total, "pct": pct,
                    }

                elif test["type"] == "order":
                    ordered, total, details = test_reading_order(text, test["phrases"])
                    pct = round(ordered / total * 100, 1) if total else 0
                    score = f"{ordered}/{total} pairs in order ({pct}%)"
                    if details:
                        score += f"  swapped: {details[:2]}"
                    parser_result["tests"][tname] = {
                        "ordered": ordered, "total": total, "pct": pct, "swaps": details[:3],
                    }

                elif test["type"] == "columns":
                    correct, total, status = test_column_separation(
                        text, test["left"], test["right"]
                    )
                    pct = round(correct / total * 100, 1) if total else 0
                    score = f"{correct}/{total} pairs correct ({pct}%) - {status}"
                    parser_result["tests"][tname] = {
                        "correct": correct, "total": total, "pct": pct, "status": status,
                    }

                print(f"    {tname}: {score}")

            suite_result["parsers"][parser_name] = parser_result
        all_results.append(suite_result)

    return all_results


def main():
    parser = argparse.ArgumentParser(
        prog="parser-bench",
        description="PDF parser benchmarking suite",
    )
    parser.add_argument(
        "--suite",
        choices=["standard", "hard", "all"],
        default="all",
        help="Which benchmark suite to run (default: all)",
    )
    parser.add_argument(
        "--parsers",
        type=str,
        default=None,
        help="Comma-separated list of parsers to test (default: all registered)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of timed runs per parser (default: 5)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Number of warmup runs per parser (default: 1)",
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default="docs",
        help="Root directory containing standard/ and hard/ PDF subdirs (default: docs)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory for output files (default: results)",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Skip dashboard HTML generation",
    )

    args = parser.parse_args()

    # Resolve parsers
    available = list_parsers()
    if args.parsers:
        requested = [p.strip() for p in args.parsers.split(",")]
        # Case-insensitive matching
        name_map = {n.lower(): n for n in available}
        parsers = []
        for r in requested:
            match = name_map.get(r.lower())
            if match:
                parsers.append(match)
            else:
                print(f"Unknown parser: {r}. Available: {', '.join(available)}")
                sys.exit(1)
    else:
        parsers = available

    env = capture_environment()
    print(f"Python {env['python'].split()[0]} on {env['platform']}")
    print(f"Parsers: {', '.join(parsers)}")
    print(f"Runs: {args.runs}, Warmup: {args.warmup}")
    standard_docs = os.path.join(args.docs_dir, "standard")
    hard_docs = os.path.join(args.docs_dir, "hard")
    print(f"Docs: {os.path.abspath(args.docs_dir)}")

    os.makedirs(args.output_dir, exist_ok=True)

    # Standard suite
    if args.suite in ("standard", "all"):
        print(f"\n{'#' * 60}")
        print("  STANDARD BENCHMARK SUITE")
        print(f"{'#' * 60}")
        standard_results = run_standard_suite(
            parsers, standard_docs, runs=args.runs, warmup=args.warmup
        )

        # Save results JSON
        out = os.path.join(args.output_dir, "results.json")
        serializable = {}
        for pdf, data in standard_results.items():
            serializable[pdf] = {
                "label": data["label"],
                "description": data["description"],
                "file_size": data["file_size"],
                "parsers": {
                    k: {kk: vv for kk, vv in v.items() if kk != "text_preview"}
                    for k, v in data["parsers"].items()
                },
            }
        with open(out, "w") as f:
            json.dump({"environment": env, "results": serializable}, f, indent=2, default=str)
        print(f"\nResults written to {out}")

        if not args.no_dashboard:
            generate_standard_dashboard(
                standard_results, env,
                output_path=os.path.join(args.output_dir, "dashboard.html"),
            )

    # Hard suite
    if args.suite in ("hard", "all"):
        print(f"\n{'#' * 60}")
        print("  HARD BENCHMARK SUITE")
        print(f"{'#' * 60}")
        hard_results = run_hard_suite(parsers, hard_docs)

        out = os.path.join(args.output_dir, "results_hard.json")
        with open(out, "w") as f:
            json.dump({"environment": env, "results": hard_results}, f, indent=2, default=str)
        print(f"\nResults written to {out}")

        if not args.no_dashboard:
            generate_hard_dashboard(
                hard_results, env,
                output_path=os.path.join(args.output_dir, "dashboard_hard.html"),
            )

    print("\nDone.")


if __name__ == "__main__":
    main()

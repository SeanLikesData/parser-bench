"""
Dashboard HTML generation for standard and hard benchmark suites.
"""

import html
import json
import statistics
import time

from .parsers import get_parser_meta, list_parsers

COLORS = {
    "PyMuPDF": "#3b82f6",
    "pdfplumber": "#10b981",
    "pypdf": "#f59e0b",
    "LiteParse": "#ef4444",
}


def _check(val):
    if val:
        return '<span class="text-green-400 font-bold">&#10003;</span>'
    return '<span class="text-red-400">&#10007;</span>'


# ── Standard dashboard ──────────────────────────────────────────


def generate_standard_dashboard(results, env, *, output_path="dashboard.html"):
    """Generate the standard benchmark dashboard.

    results: dict mapping pdf filename -> {
        label, description, file_size,
        parsers: {name -> {stats, metrics, content_found, content_total, content_pct,
                           has_bbox, bbox_count, has_tables, table_count, text_preview}}
    }
    """
    parsers_list = [p for p in list_parsers() if any(
        p in data["parsers"] for data in results.values()
    )]
    runs = None
    warmup = None
    for data in results.values():
        for pr in data["parsers"].values():
            if "error" not in pr and pr.get("stats"):
                runs = pr["stats"]["runs"]
                warmup = pr["stats"]["warmup_runs"]
                break
        if runs:
            break

    # Speed chart data
    speed_labels = []
    speed_datasets = {p: [] for p in parsers_list}
    content_datasets = {p: [] for p in parsers_list}

    for data in results.values():
        speed_labels.append(data["label"])
        for p in parsers_list:
            pr = data["parsers"].get(p, {})
            stats = pr.get("stats", {})
            speed_datasets[p].append(round(stats.get("avg_ms", 0), 1))
            content_datasets[p].append(pr.get("content_pct", 0))

    # Feature comparison
    feature_rows = []
    for p in parsers_list:
        meta = get_parser_meta(p)
        has_bbox = any(
            data["parsers"].get(p, {}).get("has_bbox", False)
            for data in results.values()
        )
        has_tables = any(
            data["parsers"].get(p, {}).get("has_tables", False)
            for data in results.values()
        )
        speeds = [
            data["parsers"][p]["stats"]["avg_ms"]
            for data in results.values()
            if p in data["parsers"] and "error" not in data["parsers"][p] and data["parsers"][p].get("stats")
        ]
        contents = [
            data["parsers"][p]["content_pct"]
            for data in results.values()
            if p in data["parsers"] and "error" not in data["parsers"][p]
        ]
        avg_speed = statistics.mean(speeds) if speeds else 0
        avg_content = statistics.mean(contents) if contents else 0

        feature_rows.append(f"""<tr class="border-b border-gray-700 hover:bg-gray-800/50">
            <td class="py-3 px-4 font-semibold" style="color:{COLORS.get(p, '#888')}">{p}</td>
            <td class="py-3 px-4 text-right">{avg_speed:.0f} ms</td>
            <td class="py-3 px-4 text-right">{avg_content:.1f}%</td>
            <td class="py-3 px-4 text-center">{_check(has_bbox)}</td>
            <td class="py-3 px-4 text-center">{_check(has_tables)}</td>
            <td class="py-3 px-4 text-center">{_check(meta['pure_python'])}</td>
            <td class="py-3 px-4 text-center">{_check(meta['multi_format'])}</td>
        </tr>""")

    # Per-file detail rows
    detail_sections = []
    for pdf_file, data in results.items():
        rows = []
        for p in parsers_list:
            pr = data["parsers"].get(p, {})
            if "error" in pr:
                rows.append(f"""<tr class="border-b border-gray-700">
                    <td class="py-2 px-3 font-medium" style="color:{COLORS.get(p, '#888')}">{p}</td>
                    <td colspan="6" class="py-2 px-3 text-red-400">Error: {html.escape(str(pr['error'])[:100])}</td>
                </tr>""")
            else:
                stats = pr.get("stats", {})
                std_str = f' <span class="text-gray-500 text-xs">&plusmn;{stats.get("std_ms", 0):.0f}</span>' if stats.get("std_ms", 0) > 0 else ""
                rows.append(f"""<tr class="border-b border-gray-700 hover:bg-gray-800/50">
                    <td class="py-2 px-3 font-medium" style="color:{COLORS.get(p, '#888')}">{p}</td>
                    <td class="py-2 px-3 text-right">{stats.get('avg_ms', 0):.0f} ms{std_str}</td>
                    <td class="py-2 px-3 text-right">{pr['metrics']['words']:,}</td>
                    <td class="py-2 px-3 text-right">{pr['metrics']['chars']:,}</td>
                    <td class="py-2 px-3 text-right">{pr['content_found']}/{pr['content_total']} ({pr['content_pct']}%)</td>
                    <td class="py-2 px-3 text-center">{'<span class="text-green-400">Yes</span> (' + str(pr['bbox_count']) + ')' if pr['has_bbox'] else '<span class="text-gray-500">No</span>'}</td>
                    <td class="py-2 px-3 text-center">{('<span class="text-green-400">' + str(pr['table_count']) + '</span>') if pr.get('has_tables') else '<span class="text-gray-500">-</span>'}</td>
                </tr>""")
        detail_sections.append(f"""
        <div class="bg-gray-900 rounded-lg p-5 border border-gray-700">
            <h3 class="text-lg font-semibold mb-1">{data['label']}</h3>
            <p class="text-gray-400 text-sm mb-3">{data['description']} - {data['file_size']/1024:.0f} KB</p>
            <table class="w-full text-sm">
                <thead><tr class="text-gray-400 border-b border-gray-600">
                    <th class="py-2 px-3 text-left">Parser</th>
                    <th class="py-2 px-3 text-right">Speed</th>
                    <th class="py-2 px-3 text-right">Words</th>
                    <th class="py-2 px-3 text-right">Chars</th>
                    <th class="py-2 px-3 text-right">Content Match</th>
                    <th class="py-2 px-3 text-center">Bounding Boxes</th>
                    <th class="py-2 px-3 text-center">Tables</th>
                </tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>""")

    # Text preview sections
    preview_sections = []
    for pdf_file, data in results.items():
        previews = []
        for p in parsers_list:
            pr = data["parsers"].get(p, {})
            if "error" not in pr and "text_preview" in pr:
                escaped = html.escape(pr["text_preview"][:400])
                previews.append(f"""
                <div class="flex-1 min-w-[280px]">
                    <h4 class="text-sm font-semibold mb-1" style="color:{COLORS.get(p, '#888')}">{p}</h4>
                    <pre class="bg-gray-800 rounded p-2 text-xs overflow-auto max-h-48 whitespace-pre-wrap">{escaped}</pre>
                </div>""")
        preview_sections.append(f"""
        <div class="bg-gray-900 rounded-lg p-5 border border-gray-700">
            <h3 class="text-lg font-semibold mb-3">{data['label']} - Text Output Preview</h3>
            <div class="flex flex-wrap gap-3">{''.join(previews)}</div>
        </div>""")

    # Environment info
    env_html = ""
    if env:
        libs = env.get("libraries", {})
        lib_str = ", ".join(f"{k} {v}" for k, v in libs.items())
        env_html = f"""
    <div class="text-center text-gray-500 text-xs mt-2 space-y-1">
        <p>{env.get('platform', '')} | {env.get('python', '').split()[0]}</p>
        <p>{lib_str}</p>
    </div>"""

    runs_str = f"{runs} runs" if runs else ""
    warmup_str = f", {warmup} warmup" if warmup else ""

    dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PDF Parser Benchmark Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body {{ background: #0f172a; color: #e2e8f0; font-family: 'Inter', system-ui, sans-serif; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; }}
</style>
</head>
<body class="min-h-screen p-6">
<div class="max-w-7xl mx-auto space-y-6">

  <div class="text-center mb-8">
    <h1 class="text-3xl font-bold mb-2">PDF Parser Benchmark</h1>
    <p class="text-gray-400">{' vs '.join(parsers_list)} - {len(results)} test documents, {runs_str}{warmup_str}</p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="card">
      <h2 class="text-xl font-semibold mb-4">Parse Speed (ms, lower is better)</h2>
      <canvas id="speedChart" height="250"></canvas>
    </div>
    <div class="card">
      <h2 class="text-xl font-semibold mb-4">Content Accuracy (%, higher is better)</h2>
      <canvas id="contentChart" height="250"></canvas>
    </div>
  </div>

  <div class="card">
    <h2 class="text-xl font-semibold mb-4">Feature Comparison</h2>
    <table class="w-full text-sm">
      <thead><tr class="text-gray-400 border-b border-gray-600">
        <th class="py-3 px-4 text-left">Parser</th>
        <th class="py-3 px-4 text-right">Avg Speed</th>
        <th class="py-3 px-4 text-right">Avg Content Match</th>
        <th class="py-3 px-4 text-center">Bounding Boxes</th>
        <th class="py-3 px-4 text-center">Table Extraction</th>
        <th class="py-3 px-4 text-center">Pure Python</th>
        <th class="py-3 px-4 text-center">Multi-Format</th>
      </tr></thead>
      <tbody>{''.join(feature_rows)}</tbody>
    </table>
  </div>

  <h2 class="text-xl font-semibold mt-8">Per-Document Results</h2>
  <div class="space-y-4">
    {''.join(detail_sections)}
  </div>

  <h2 class="text-xl font-semibold mt-8">Text Output Comparison</h2>
  <div class="space-y-4">
    {''.join(preview_sections)}
  </div>

  <p class="text-center text-gray-500 text-sm mt-8">
    Benchmark run on {env.get('timestamp', time.strftime('%Y-%m-%d %H:%M'))}
  </p>
  {env_html}
</div>

<script>
const speedLabels = {json.dumps(speed_labels)};
const speedDatasets = [
  {','.join(
    '{' + f'label:"{p}",data:{json.dumps(speed_datasets[p])},backgroundColor:"{COLORS.get(p, "#888")}",borderColor:"{COLORS.get(p, "#888")}",borderWidth:1' + '}'
    for p in parsers_list
  )}
];
const contentDatasets = [
  {','.join(
    '{' + f'label:"{p}",data:{json.dumps(content_datasets[p])},backgroundColor:"{COLORS.get(p, "#888")}",borderColor:"{COLORS.get(p, "#888")}",borderWidth:1' + '}'
    for p in parsers_list
  )}
];

const chartOpts = {{
  responsive: true,
  plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }},
  scales: {{
    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
    y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }}, beginAtZero: true }}
  }}
}};

new Chart(document.getElementById('speedChart'), {{
  type: 'bar', data: {{ labels: speedLabels, datasets: speedDatasets }},
  options: {{ ...chartOpts, scales: {{ ...chartOpts.scales, y: {{ ...chartOpts.scales.y, type: 'logarithmic', title: {{ display: true, text: 'ms (log scale)', color: '#94a3b8' }} }} }} }}
}});

new Chart(document.getElementById('contentChart'), {{
  type: 'bar', data: {{ labels: speedLabels, datasets: contentDatasets }},
  options: {{ ...chartOpts, scales: {{ ...chartOpts.scales, y: {{ ...chartOpts.scales.y, max: 100, title: {{ display: true, text: '% phrases found', color: '#94a3b8' }} }} }} }}
}});
</script>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(dashboard_html)
    print(f"Dashboard written to {output_path}")


# ── Hard dashboard ──────────────────────────────────────────────


def generate_hard_dashboard(all_results, env, *, output_path="dashboard_hard.html"):
    """Generate the hard benchmark dashboard.

    all_results: list of suite dicts [{file, label, file_size, parsers: {name -> {time_ms, words, chars, pages, tests}}}]
    """
    parsers_list = [p for p in list_parsers() if any(
        p in suite["parsers"] for suite in all_results
    )]

    # Aggregate scores
    aggregate = {p: {"speed": [], "test_scores": [], "test_count": 0} for p in parsers_list}
    for suite in all_results:
        for pname in parsers_list:
            pr = suite["parsers"].get(pname, {})
            if "error" in pr:
                continue
            aggregate[pname]["speed"].append(pr["time_ms"])
            for tres in pr.get("tests", {}).values():
                pct = tres.get("pct", tres.get("score_pct", 0))
                penalty = tres.get("penalty", 0) * 5
                aggregate[pname]["test_scores"].append(max(0, pct - penalty))
                aggregate[pname]["test_count"] += 1

    # Detail HTML
    detail_html = []
    for suite in all_results:
        tests_in_suite = []
        if suite["parsers"]:
            first_parser = next(iter(suite["parsers"].values()))
            if "error" not in first_parser:
                tests_in_suite = list(first_parser.get("tests", {}).keys())

        test_headers = "".join(f'<th class="py-2 px-3 text-center text-xs">{t}</th>' for t in tests_in_suite)

        rows = []
        for pname in parsers_list:
            pr = suite["parsers"].get(pname, {})
            if "error" in pr:
                rows.append(f'''<tr class="border-b border-gray-700">
                    <td class="py-2 px-3 font-medium" style="color:{COLORS.get(pname, '#888')}">{pname}</td>
                    <td class="py-2 px-3 text-right">-</td>
                    <td class="py-2 px-3 text-right">-</td>
                    <td colspan="{len(tests_in_suite)}" class="py-2 px-3 text-red-400 text-xs">Error: {html.escape(str(pr["error"])[:80])}</td>
                </tr>''')
                continue

            test_cells = []
            for tname in tests_in_suite:
                tres = pr.get("tests", {}).get(tname, {})
                pct = tres.get("pct", tres.get("score_pct", 0))
                penalty = tres.get("penalty", 0)

                if pct >= 90 and penalty == 0:
                    cls = "text-green-400"
                elif pct >= 70:
                    cls = "text-yellow-400"
                else:
                    cls = "text-red-400"

                detail = ""
                if "found" in tres and "total" in tres:
                    detail = f'{tres["found"]}/{tres["total"]}'
                elif "ordered" in tres:
                    detail = f'{tres["ordered"]}/{tres["total"]}'
                elif "correct" in tres:
                    detail = f'{tres["correct"]}/{tres["total"]}'
                    if tres.get("status") == "interleaved":
                        cls = "text-red-400"
                elif "content_found" in tres:
                    detail = f'{tres["content_found"]}/{tres["content_total"]}'
                    if penalty > 0:
                        detail += f' !{tres["interleaved"]}'
                        cls = "text-yellow-400"

                missing = tres.get("missing", [])
                swaps = tres.get("swaps", [])
                tooltip = ""
                if missing:
                    tooltip = f' title="Missing: {html.escape(", ".join(str(m) for m in missing[:3]))}"'
                elif swaps:
                    tooltip = f' title="Swapped: {html.escape(", ".join(swaps[:2]))}"'

                test_cells.append(
                    f'<td class="py-2 px-3 text-center {cls} text-xs cursor-help"{tooltip}>'
                    f'{detail} <span class="text-gray-500">({pct}%)</span></td>'
                )

            rows.append(f'''<tr class="border-b border-gray-700 hover:bg-gray-800/50">
                <td class="py-2 px-3 font-medium" style="color:{COLORS.get(pname, '#888')}">{pname}</td>
                <td class="py-2 px-3 text-right">{pr["time_ms"]:.0f} ms</td>
                <td class="py-2 px-3 text-right">{pr["words"]:,}</td>
                {''.join(test_cells)}
            </tr>''')

        detail_html.append(f'''
        <div class="bg-gray-900 rounded-lg p-5 border border-gray-700">
            <h3 class="text-lg font-semibold mb-1">{suite["label"]}</h3>
            <p class="text-gray-400 text-sm mb-3">{suite["file"]} - {suite["file_size"]/1024:.0f} KB</p>
            <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead><tr class="text-gray-400 border-b border-gray-600">
                    <th class="py-2 px-3 text-left">Parser</th>
                    <th class="py-2 px-3 text-right">Speed</th>
                    <th class="py-2 px-3 text-right">Words</th>
                    {test_headers}
                </tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
            </div>
        </div>''')

    # Text preview sections
    preview_sections = []
    for suite in all_results:
        previews = []
        for pname in parsers_list:
            pr = suite["parsers"].get(pname, {})
            if "error" not in pr and pr.get("text_preview"):
                escaped = html.escape(pr["text_preview"][:400])
                previews.append(f"""
                <div class="flex-1 min-w-[280px]">
                    <h4 class="text-sm font-semibold mb-1" style="color:{COLORS.get(pname, '#888')}">{pname}</h4>
                    <pre class="bg-gray-800 rounded p-2 text-xs overflow-auto max-h-48 whitespace-pre-wrap">{escaped}</pre>
                </div>""")
        if previews:
            preview_sections.append(f"""
        <div class="bg-gray-900 rounded-lg p-5 border border-gray-700">
            <h3 class="text-lg font-semibold mb-3">{suite['label']} - Text Output Preview</h3>
            <div class="flex flex-wrap gap-3">{''.join(previews)}</div>
        </div>""")

    # Scorecard
    scorecard_rows = []
    for pname in parsers_list:
        agg = aggregate[pname]
        avg_speed = statistics.mean(agg["speed"]) if agg["speed"] else 0
        avg_score = statistics.mean(agg["test_scores"]) if agg["test_scores"] else 0
        n_tests = agg["test_count"]

        if avg_speed < 100:
            speed_badge = '<span class="bg-green-900 text-green-300 px-2 py-0.5 rounded text-xs">Excellent</span>'
        elif avg_speed < 500:
            speed_badge = '<span class="bg-blue-900 text-blue-300 px-2 py-0.5 rounded text-xs">Good</span>'
        elif avg_speed < 2000:
            speed_badge = '<span class="bg-yellow-900 text-yellow-300 px-2 py-0.5 rounded text-xs">Slow</span>'
        else:
            speed_badge = '<span class="bg-red-900 text-red-300 px-2 py-0.5 rounded text-xs">Very Slow</span>'

        if avg_score >= 95:
            quality_badge = '<span class="bg-green-900 text-green-300 px-2 py-0.5 rounded text-xs">Excellent</span>'
        elif avg_score >= 85:
            quality_badge = '<span class="bg-blue-900 text-blue-300 px-2 py-0.5 rounded text-xs">Good</span>'
        elif avg_score >= 70:
            quality_badge = '<span class="bg-yellow-900 text-yellow-300 px-2 py-0.5 rounded text-xs">Fair</span>'
        else:
            quality_badge = '<span class="bg-red-900 text-red-300 px-2 py-0.5 rounded text-xs">Poor</span>'

        scorecard_rows.append(f'''<tr class="border-b border-gray-700">
            <td class="py-3 px-4 font-semibold text-lg" style="color:{COLORS.get(pname, '#888')}">{pname}</td>
            <td class="py-3 px-4 text-right">{avg_speed:.0f} ms {speed_badge}</td>
            <td class="py-3 px-4 text-right">{avg_score:.1f}% {quality_badge}</td>
            <td class="py-3 px-4 text-right text-gray-400">{n_tests} tests</td>
        </tr>''')

    # Chart data
    speed_labels = [s["label"][:25] for s in all_results]
    speed_data = {p: [] for p in parsers_list}
    quality_data = {p: [] for p in parsers_list}
    for suite in all_results:
        for p in parsers_list:
            pr = suite["parsers"].get(p, {})
            speed_data[p].append(pr.get("time_ms", 0))
            if "error" in pr or not pr.get("tests"):
                quality_data[p].append(0)
            else:
                scores = [t.get("pct", t.get("score_pct", 0)) for t in pr["tests"].values()]
                quality_data[p].append(round(statistics.mean(scores), 1) if scores else 0)

    # Environment info
    env_html = ""
    if env:
        libs = env.get("libraries", {})
        lib_str = ", ".join(f"{k} {v}" for k, v in libs.items())
        env_html = f"""
    <div class="text-center text-gray-500 text-xs mt-2 space-y-1">
        <p>{env.get('platform', '')} | {env.get('python', '').split()[0]}</p>
        <p>{lib_str}</p>
    </div>"""

    total_tests = sum(len(s.get("tests", [])) for s in all_results if isinstance(s.get("tests"), list))
    # If tests is in the all_results items directly (from HARD_TESTS structure), count from source
    if total_tests == 0:
        from .tests import HARD_TESTS
        total_tests = sum(len(s.get("tests", [])) for s in HARD_TESTS)

    dashboard = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PDF Parser Benchmark - Hard Tests</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body {{ background: #0f172a; color: #e2e8f0; }}
  [title] {{ cursor: help; }}
</style>
</head>
<body class="min-h-screen p-6">
<div class="max-w-7xl mx-auto space-y-6">

  <div class="text-center mb-8">
    <h1 class="text-3xl font-bold mb-2">PDF Parser Benchmark - Hard Mode</h1>
    <p class="text-gray-400">Testing reading order, column handling, numeric extraction, table fidelity, and watermark filtering</p>
    <p class="text-gray-500 text-sm mt-1">{len(all_results)} documents, {total_tests} quality tests</p>
  </div>

  <div class="bg-gray-900 rounded-lg p-6 border border-gray-700">
    <h2 class="text-xl font-semibold mb-4">Overall Scorecard</h2>
    <table class="w-full">
      <thead><tr class="text-gray-400 border-b border-gray-600">
        <th class="py-2 px-4 text-left">Parser</th>
        <th class="py-2 px-4 text-right">Avg Speed</th>
        <th class="py-2 px-4 text-right">Avg Quality Score</th>
        <th class="py-2 px-4 text-right">Tests Run</th>
      </tr></thead>
      <tbody>{''.join(scorecard_rows)}</tbody>
    </table>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-gray-900 rounded-lg p-5 border border-gray-700">
      <h2 class="text-lg font-semibold mb-3">Parse Speed by Document (ms, log scale)</h2>
      <canvas id="speedChart" height="280"></canvas>
    </div>
    <div class="bg-gray-900 rounded-lg p-5 border border-gray-700">
      <h2 class="text-lg font-semibold mb-3">Quality Score by Document (%)</h2>
      <canvas id="qualityChart" height="280"></canvas>
    </div>
  </div>

  <h2 class="text-xl font-semibold mt-8 mb-2">Detailed Results by Document</h2>
  <p class="text-gray-400 text-sm mb-4">Hover over scores to see missing items. Colors: <span class="text-green-400">green</span> >=90%, <span class="text-yellow-400">yellow</span> >=70%, <span class="text-red-400">red</span> &lt;70%</p>
  <div class="space-y-4">
    {''.join(detail_html)}
  </div>

  <h2 class="text-xl font-semibold mt-8 mb-2">Text Output Comparison</h2>
  <div class="space-y-4">
    {''.join(preview_sections)}
  </div>

  <div class="mt-10 p-5 bg-gray-900 rounded-lg border border-gray-700">
    <h2 class="text-lg font-semibold mb-3">Test Methodology</h2>
    <div class="text-sm text-gray-400 space-y-2">
      <p><strong class="text-gray-300">Numeric Extraction:</strong> Checks if specific values (dollar amounts, percentages, citations) appear verbatim in extracted text.</p>
      <p><strong class="text-gray-300">Table Row Integrity:</strong> Verifies that values belonging to the same table row appear on the same line in the output.</p>
      <p><strong class="text-gray-300">Reading Order:</strong> Tests that phrases appear in the correct sequential order (important for multi-column and complex layouts).</p>
      <p><strong class="text-gray-300">Column Separation:</strong> For two-column documents, checks if left column is fully read before right column (vs interleaved line-by-line reading).</p>
      <p><strong class="text-gray-300">Watermark Separation:</strong> Checks if watermark text is cleanly separated from content text, with penalties for interleaving.</p>
    </div>
  </div>

  <p class="text-center text-gray-500 text-sm mt-8">
    Benchmark run on {env.get('timestamp', time.strftime('%Y-%m-%d %H:%M'))}
  </p>
  {env_html}
</div>

<script>
const labels = {json.dumps(speed_labels)};
const colors = {json.dumps({p: COLORS.get(p, '#888') for p in parsers_list})};
const parsers = {json.dumps(parsers_list)};

function makeDatasets(dataMap) {{
  return parsers.map(p => ({{
    label: p,
    data: dataMap[p],
    backgroundColor: colors[p],
    borderColor: colors[p],
    borderWidth: 1
  }}));
}}

const chartOpts = {{
  responsive: true,
  plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }},
  scales: {{
    x: {{ ticks: {{ color: '#94a3b8', maxRotation: 45 }}, grid: {{ color: '#1e293b' }} }},
    y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }}, beginAtZero: true }}
  }}
}};

new Chart(document.getElementById('speedChart'), {{
  type: 'bar',
  data: {{ labels, datasets: makeDatasets({json.dumps(speed_data)}) }},
  options: {{ ...chartOpts, scales: {{ ...chartOpts.scales, y: {{ ...chartOpts.scales.y, type: 'logarithmic' }} }} }}
}});

new Chart(document.getElementById('qualityChart'), {{
  type: 'bar',
  data: {{ labels, datasets: makeDatasets({json.dumps(quality_data)}) }},
  options: {{ ...chartOpts, scales: {{ ...chartOpts.scales, y: {{ ...chartOpts.scales.y, max: 100 }} }} }}
}});
</script>
</body>
</html>'''

    with open(output_path, "w") as f:
        f.write(dashboard)
    print(f"Dashboard written to {output_path}")

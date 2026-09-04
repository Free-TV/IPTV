#!/usr/bin/python3
"""Turn `.github/checker-history/history.jsonl` into a static status dashboard.

Reads the JSON-lines history that `check_channels.py --json` appends to (one row
per channel per run), and writes a single self-contained `docs/index.html`: no
build step, no client-side fetch of the raw history - everything needed to render
is computed here and baked into the page, so it opens instantly whether it is
opened from disk or served by GitHub Pages.

The page shows:
  - today's state breakdown (how many channels are alive/dead/blocked/... right now)
  - a trend of the alive share across every run kept in the history
  - one row per list (country) with its current breakdown
  - every channel that is not currently `alive`, searchable and filterable by state

"Currently" means: for each (list, channel), the most recent row in the history -
older rows for the same channel are trend data, not part of today's snapshot.

Usage:
    ./generate_dashboard.py                          # reads the default history path
    ./generate_dashboard.py --history path/to.jsonl --out path/to.html
"""

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from html import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HISTORY = os.path.join(BASE_DIR, ".github", "checker-history", "history.jsonl")
DEFAULT_OUT = os.path.join(BASE_DIR, "docs", "index.html")

# rendering order and the CSS custom property carrying each state's color
STATE_ORDER = ["alive", "flaky", "blocked", "unreachable", "disputed", "dead"]
STATE_VAR = {s: f"var(--s-{s})" for s in STATE_ORDER}
STATE_LABEL = {
    "alive": "answers every time",
    "flaky": "answers, but not every time",
    "blocked": "refused - likely geo-restricted",
    "unreachable": "times out or refuses to connect",
    "disputed": "looked dead, ffprobe found a stream - needs a human",
    "dead": "gone on every attempt, ffprobe agrees where asked",
}


def read_history(path):
    """Return every row of the history file, oldest first, skipping malformed lines."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    rows.sort(key=lambda r: r["checked_at"])
    return rows


def latest_snapshot(rows):
    """Return the most recent row for each (list, channel, url) tuple."""
    latest = {}
    for row in rows:
        key = (row["list"], row["channel"], row["url"])
        latest[key] = row
    return list(latest.values())


def run_trend(rows):
    """Group rows by `checked_at` (one run) and return the alive share of each run."""
    by_run = defaultdict(lambda: defaultdict(int))
    for row in rows:
        by_run[row["checked_at"]][row["state"]] += 1
    points = []
    for checked_at in sorted(by_run):
        counts = by_run[checked_at]
        total = sum(counts.values())
        alive_share = counts.get("alive", 0) / total if total else 0
        points.append((checked_at, alive_share, total))
    return points


def _scope_grid_and_labels(pad_l, pad_r, pad_t, width, plot_h):
    """Return the horizontal gridlines and their %-axis labels for `svg_trend`."""
    grid = "".join(
        f'<line x1="{pad_l}" y1="{pad_t + plot_h * f:.1f}" '
        f'x2="{width - pad_r}" y2="{pad_t + plot_h * f:.1f}" class="scope-grid"/>'
        for f in (0, 0.25, 0.5, 0.75, 1)
    )
    labels = "".join(
        f'<text x="{pad_l - 8}" y="{pad_t + plot_h * f + 4:.1f}" class="scope-axis" '
        f'text-anchor="end">{int((1 - f) * 100)}%</text>'
        for f in (0, 0.5, 1)
    )
    return grid, labels


def _scope_geometry(points, pad_l, pad_t, plot_w, plot_h):
    """Return `(line_path, area_path, last_x, last_y)` for the trend's data points."""
    xs = [pad_l + i * plot_w / (len(points) - 1) for i in range(len(points))]
    ys = [pad_t + (1 - share) * plot_h for _, share, _ in points]
    steps = (f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    path = " ".join(steps)
    area = path + f" L{xs[-1]:.1f},{pad_t + plot_h:.1f} L{xs[0]:.1f},{pad_t + plot_h:.1f} Z"
    return path, area, xs[-1], ys[-1]


def _scope_endpoint_labels(points):
    """Return `(first_date, last_date, last_alive_pct)` for the trend's endpoints."""
    return points[0][0][:10], points[-1][0][:10], f"{points[-1][1] * 100:.1f}%"


def svg_trend(points, width=860, height=180):
    """Render `points` as an oscilloscope-style trace of the alive share over time.

    Kept as one function despite the local-variable count: it is a single visual
    composite (grid, axis labels, line, fill, endpoint dot) whose pieces only make
    sense read together, and splitting it further would trade a readable layout
    calculation for indirection between fragments that all belong to one <svg>.
    """
    # pylint: disable=too-many-locals
    pad_l, pad_r, pad_t = 34, 16, 16
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - 26
    grid, labels = _scope_grid_and_labels(pad_l, pad_r, pad_t, width, plot_h)

    if len(points) < 2:
        return (
            f'<svg viewBox="0 0 {width} {height}" class="scope" role="img" '
            f'aria-label="Not enough runs yet for a trend">{grid}{labels}'
            f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" class="scope-empty">'
            "collecting data - check back after a few runs</text></svg>"
        )

    path, area, last_x, last_y = _scope_geometry(points, pad_l, pad_t, plot_w, plot_h)
    first_label, last_label, last_pct = _scope_endpoint_labels(points)
    return (
        f'<svg viewBox="0 0 {width} {height}" class="scope" role="img" aria-label='
        f'"Alive share over time, {first_label} to {last_label}, currently {last_pct}">'
        f"{grid}{labels}"
        f'<path d="{area}" class="scope-fill"/><path d="{path}" class="scope-line"/>'
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3.5" class="scope-dot"/>'
        f'<text x="{pad_l}" y="{height - 6}" class="scope-axis">{escape(first_label)}</text>'
        f'<text x="{width - pad_r}" y="{height - 6}" class="scope-axis" text-anchor="end">'
        f"{escape(last_label)}</text></svg>"
    )


def svg_signal_bar(counts, width=280, height=14):
    """Render a `state -> count` mapping as one horizontal signal-strength bar."""
    total = sum(counts.values()) or 1
    x = 0
    segments = []
    for state in STATE_ORDER:
        count = counts.get(state, 0)
        if not count:
            continue
        w = count / total * width
        segments.append(
            f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="{height}" fill="{STATE_VAR[state]}">'
            f"<title>{state}: {count} ({count / total * 100:.1f}%)</title></rect>"
        )
        x += w
    return (
        f'<svg viewBox="0 0 {width} {height}" class="signal-bar" role="img" '
        f'aria-label="State breakdown">{"".join(segments)}</svg>'
    )


def legend_html():
    """Return the small state-color legend shown above the by-list table."""
    chips = "".join(
        f'<span class="chip"><span class="dot" style="background:{STATE_VAR[s]}"></span>{s}'
        f'<span class="chip-note">{STATE_LABEL[s]}</span></span>'
        for s in STATE_ORDER
    )
    return f'<div class="legend">{chips}</div>'


# pylint: disable=line-too-long
EMPTY_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Channel Signal</title>
<style>body{{font-family:system-ui;padding:3rem;background:#0f1417;color:#e7edf0}}</style></head>
<body><h1>Channel Signal</h1><p>No history yet at {path} - the checker workflows populate this after their first run.</p></body></html>"""
# pylint: enable=line-too-long


def build_cards(overall_counts):
    """Return the row of big per-state count cards at the top of the page."""
    return "".join(
        f'<div class="card"><div class="card-num" style="color:{STATE_VAR[s]}">'
        f'{overall_counts.get(s, 0)}</div><div class="card-label">{s}</div></div>'
        for s in STATE_ORDER
    )


def build_list_rows(by_list):
    """Return one `<tr>` per list (country), each with its own signal bar."""
    rows = []
    for name in sorted(by_list):
        entries = by_list[name]
        counts = defaultdict(int)
        for entry in entries:
            counts[entry["state"]] += 1
        alive_pct = counts.get("alive", 0) / len(entries) * 100
        rows.append(
            f"<tr><td class='list-name'>{escape(name)}</td><td class='num'>{len(entries)}</td>"
            f'<td class="num" style="color:{STATE_VAR["alive"]}">{alive_pct:.0f}%</td>'
            f"<td>{svg_signal_bar(counts)}</td></tr>"
        )
    return "".join(rows)


def build_problem_rows(current):
    """Return one `<tr>` per channel that is not currently `alive`."""
    ordered = sorted(current, key=lambda r: (r["state"] != "dead", r["list"], r["channel"]))
    rows = []
    for row in ordered:
        if row["state"] == "alive":
            continue
        rows.append(
            f'<tr data-state="{escape(row["state"])}">'
            f'<td>{escape(row["list"])}</td>'
            f'<td>{escape(row["channel"])}</td>'
            f'<td><span class="pill" style="background:{STATE_VAR[row["state"]]}">'
            f'{escape(row["state"])}</span></td>'
            f'<td class="url"><a href="{escape(row["url"])}">{escape(row["url"])}</a></td>'
            f'<td class="dim">{escape(row["checked_at"][:10])}</td>'
            "</tr>"
        )
    return "".join(rows)


def render(history_path, generated_at):
    """Build the full dashboard page for the history found at `history_path`."""
    rows = read_history(history_path)
    if not rows:
        return EMPTY_PAGE.format(path=escape(history_path))

    current = latest_snapshot(rows)
    overall_counts = defaultdict(int)
    for row in current:
        overall_counts[row["state"]] += 1
    total_channels = len(current)

    by_list = defaultdict(list)
    for row in current:
        by_list[row["list"]].append(row)

    trend = run_trend(rows)
    last_checked = rows[-1]["checked_at"]
    alive_pct_overall = (
        overall_counts.get("alive", 0) / total_channels * 100 if total_channels else 0
    )

    cards = build_cards(overall_counts)
    list_rows = build_list_rows(by_list)
    problem_rows = build_problem_rows(current)
    state_options = "".join(
        f'<option value="{s}">{s}</option>' for s in STATE_ORDER if s != "alive"
    )

    # pylint: disable=line-too-long
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Channel Signal</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --bg: #f5f3ef;
  --surface: #ffffff;
  --surface-2: #edeae4;
  --text: #191d1f;
  --text-dim: #5c6a70;
  --border: #dfdad2;
  --accent: #0f766e;
  --accent-soft: #d6f3ef;
  --s-alive: #157a3d;
  --s-flaky: #b3620a;
  --s-blocked: #1d5fd6;
  --s-unreachable: #737f89;
  --s-disputed: #a324ab;
  --s-dead: #c22222;
  --shadow: 0 1px 2px rgba(30,25,15,.06), 0 6px 20px -8px rgba(30,25,15,.12);
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #10181a;
    --surface: #16211f;
    --surface-2: #1b2725;
    --text: #eaf2ee;
    --text-dim: #8fa39d;
    --border: #253634;
    --accent: #2dd4bf;
    --accent-soft: #123934;
    --s-alive: #4ade80;
    --s-flaky: #fbbf24;
    --s-blocked: #60a5fa;
    --s-unreachable: #93a4ab;
    --s-disputed: #e879f9;
    --s-dead: #f87171;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px -8px rgba(0,0,0,.5);
  }}
}}
:root[data-theme="dark"] {{
  --bg: #10181a;
  --surface: #16211f;
  --surface-2: #1b2725;
  --text: #eaf2ee;
  --text-dim: #8fa39d;
  --border: #253634;
  --accent: #2dd4bf;
  --accent-soft: #123934;
  --s-alive: #4ade80;
  --s-flaky: #fbbf24;
  --s-blocked: #60a5fa;
  --s-unreachable: #93a4ab;
  --s-disputed: #e879f9;
  --s-dead: #f87171;
  --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px -8px rgba(0,0,0,.5);
}}

* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--text);
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  padding: 2.5rem 1.25rem 5rem;
}}
main {{ max-width: 980px; margin: 0 auto; }}

.masthead {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: .5rem 1.5rem; margin-bottom: .35rem; }}
h1 {{
  font-family: "Archivo", system-ui, sans-serif; font-weight: 700; font-size: 1.55rem;
  letter-spacing: -.01em; margin: 0; text-wrap: balance;
}}
h1 .on-air {{ color: var(--accent); font-variant-numeric: tabular-nums; }}
.subline {{ color: var(--text-dim); font-size: .82rem; margin: 0 0 1.75rem; font-family: "IBM Plex Mono", monospace; }}

.cards {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: .6rem; margin-bottom: 1.75rem; }}
.card {{
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  padding: .85rem .5rem; text-align: center; box-shadow: var(--shadow);
}}
.card-num {{ font-family: "IBM Plex Mono", monospace; font-size: 1.7rem; font-weight: 500; font-variant-numeric: tabular-nums; line-height: 1; }}
.card-label {{ font-size: .72rem; color: var(--text-dim); margin-top: .35rem; text-transform: uppercase; letter-spacing: .06em; }}

section {{
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 1.4rem 1.6rem; margin-bottom: 1.5rem; box-shadow: var(--shadow);
}}
section h2 {{
  font-family: "Archivo", system-ui, sans-serif; font-weight: 700; font-size: 1rem;
  margin: 0 0 .9rem; letter-spacing: -.005em;
}}
.section-note {{ color: var(--text-dim); font-size: .82rem; margin: -.5rem 0 1rem; }}
.section-note code {{ font-family: "IBM Plex Mono", monospace; font-size: .8em; background: var(--surface-2); padding: .05rem .3rem; border-radius: 4px; }}

.scope {{ width: 100%; height: auto; display: block; }}
.scope-grid {{ stroke: var(--border); stroke-width: 1; }}
.scope-axis {{ font: 10.5px "IBM Plex Mono", monospace; fill: var(--text-dim); }}
.scope-empty {{ font: 12px "IBM Plex Mono", monospace; fill: var(--text-dim); }}
.scope-fill {{ fill: var(--accent-soft); }}
.scope-line {{ fill: none; stroke: var(--accent); stroke-width: 2; }}
.scope-dot {{ fill: var(--accent); }}

.legend {{ display: flex; gap: 1.1rem; flex-wrap: wrap; margin-bottom: 1rem; font-size: .78rem; }}
.chip {{ display: inline-flex; align-items: baseline; gap: .4rem; font-family: "IBM Plex Mono", monospace; color: var(--text); }}
.chip-note {{ color: var(--text-dim); font-family: "IBM Plex Sans", sans-serif; }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; align-self: center; }}

table {{ width: 100%; border-collapse: collapse; font-size: .87rem; }}
th {{
  text-align: left; padding: .4rem .55rem; border-bottom: 2px solid var(--border);
  font-size: .72rem; text-transform: uppercase; letter-spacing: .05em; color: var(--text-dim); font-weight: 600;
}}
td {{ padding: .45rem .55rem; border-bottom: 1px solid var(--border); vertical-align: middle; }}
tr:last-child td {{ border-bottom: none; }}
td.num {{ text-align: right; font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums; }}
td.list-name {{ font-weight: 500; }}
td.url {{ max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: "IBM Plex Mono", monospace; font-size: .8rem; }}
td.url a {{ color: var(--text-dim); text-decoration: none; }}
td.url a:hover {{ color: var(--accent); text-decoration: underline; }}
td.dim {{ color: var(--text-dim); font-family: "IBM Plex Mono", monospace; font-size: .8rem; }}
.signal-bar {{ width: 100%; max-width: 280px; height: 14px; display: block; border-radius: 3px; overflow: hidden; }}

.pill {{
  color: #08130f; font-family: "IBM Plex Mono", monospace; font-weight: 500;
  border-radius: 4px; padding: .12rem .5rem; font-size: .76rem; display: inline-block;
}}

.controls {{ display: flex; gap: .6rem; margin-bottom: .9rem; flex-wrap: wrap; }}
input, select {{
  padding: .45rem .6rem; border-radius: 6px; border: 1px solid var(--border);
  background: var(--surface-2); color: var(--text); font-size: .85rem; font-family: inherit;
}}
input:focus, select:focus {{ outline: 2px solid var(--accent); outline-offset: 1px; }}
#search {{ flex: 1; min-width: 180px; }}
.table-wrap {{ overflow-x: auto; }}

footer {{ text-align: center; color: var(--text-dim); font-size: .78rem; margin-top: 2.5rem; font-family: "IBM Plex Mono", monospace; }}
footer a {{ color: var(--accent); }}

@media (max-width: 720px) {{
  .cards {{ grid-template-columns: repeat(3, 1fr); }}
}}
</style>
</head>
<body>
<main>
  <div class="masthead">
    <h1>Channel Signal <span class="on-air">&mdash; {alive_pct_overall:.0f}% on air</span></h1>
  </div>
  <p class="subline">{total_channels} channels &middot; {len(by_list)} lists &middot; last swept {escape(last_checked)} &middot; page built {escape(generated_at)}</p>

  <div class="cards">{cards}</div>

  <section>
    <h2>Alive share, over time</h2>
    {svg_trend(trend)}
  </section>

  <section>
    <h2>By list</h2>
    {legend_html()}
    <div class="table-wrap">
    <table>
      <thead><tr><th>List</th><th>Channels</th><th>Alive</th><th>Signal</th></tr></thead>
      <tbody>{"".join(list_rows)}</tbody>
    </table>
    </div>
  </section>

  <section>
    <h2>Needs attention</h2>
    <p class="section-note"><code>blocked</code> usually means geo-restricted on purpose (the Ⓖ marker in the lists), not broken.
       <code>disputed</code> looked dead over HTTP but ffprobe found a real stream behind it - worth a human look before touching it.</p>
    <div class="controls">
      <input type="search" id="search" placeholder="Search list or channel&hellip;">
      <select id="state-filter">
        <option value="">All states</option>
        {state_options}
      </select>
    </div>
    <div class="table-wrap">
    <table id="problems">
      <thead><tr><th>List</th><th>Channel</th><th>State</th><th>URL</th><th>Last checked</th></tr></thead>
      <tbody>{"".join(problem_rows)}</tbody>
    </table>
    </div>
  </section>

  <footer>generated by <a href="https://github.com/Free-TV/IPTV/blob/master/check_channels.py">check_channels.py</a></footer>
</main>
<script>
  const search = document.getElementById('search');
  const stateFilter = document.getElementById('state-filter');
  const rows = [...document.querySelectorAll('#problems tbody tr')];
  function applyFilters() {{
    const q = search.value.trim().toLowerCase();
    const state = stateFilter.value;
    for (const row of rows) {{
      const matchesText = !q || row.textContent.toLowerCase().includes(q);
      const matchesState = !state || row.dataset.state === state;
      row.style.display = (matchesText && matchesState) ? '' : 'none';
    }}
  }}
  search.addEventListener('input', applyFilters);
  stateFilter.addEventListener('change', applyFilters);
</script>
</body>
</html>
"""
    # pylint: enable=line-too-long


def main():
    """Generate the dashboard from the command-line-given (or default) history path."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--history", default=DEFAULT_HISTORY, help="path to history.jsonl")
    parser.add_argument("--out", default=DEFAULT_OUT, help="path to write the dashboard HTML")
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    html = render(args.history, generated_at)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

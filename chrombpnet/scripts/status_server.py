#!/usr/bin/env python3
"""Serve a live status dashboard for the latest ChromBPNet run."""

import argparse
import base64
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

from flask import Flask, jsonify, render_template_string


def decode_metadata_path_name(encoded):
    pad_len = (-len(encoded)) % 4
    padded = encoded + ("=" * pad_len)
    try:
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
    except Exception:
        return None


def latest_snakemake_log(log_dir):
    if not os.path.isdir(log_dir):
        return None
    logs = [os.path.join(log_dir, x) for x in os.listdir(log_dir) if x.endswith(".log")]
    if not logs:
        return None
    return max(logs, key=os.path.getmtime)


def parse_job_stats_table(log_path):
    if not log_path or not os.path.exists(log_path):
        return {}
    with open(log_path) as handle:
        text = handle.read()

    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "Job stats:":
            start = i
            break
    if start is None:
        return {}

    stats = {}
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            if stats:
                break
            continue
        if stripped.startswith("job") or stripped.startswith("-----") or stripped.startswith("total"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        rule = " ".join(parts[:-1])
        if not re.fullmatch(r"\d+", parts[-1]):
            continue
        stats[rule] = int(parts[-1])
    return stats


def collect_incomplete_outputs(snakemake_dir, out_dir):
    incomplete_dir = os.path.join(snakemake_dir, "incomplete")
    out_dir_abs = os.path.abspath(out_dir)
    outputs = set()
    if not os.path.isdir(incomplete_dir):
        return outputs
    for name in os.listdir(incomplete_dir):
        decoded = decode_metadata_path_name(name)
        if decoded and os.path.abspath(decoded).startswith(out_dir_abs):
            outputs.add(os.path.abspath(decoded))
    return outputs


def collect_runtime_rows(snakemake_dir, out_dir):
    metadata_dir = os.path.join(snakemake_dir, "metadata")
    out_dir_abs = os.path.abspath(out_dir)
    incomplete_outputs = collect_incomplete_outputs(snakemake_dir, out_dir)

    rows = []
    if not os.path.isdir(metadata_dir):
        return rows

    for name in os.listdir(metadata_dir):
        path = os.path.join(metadata_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as handle:
                data = json.load(handle)
        except Exception:
            continue

        outputs = data.get("output") or []
        if isinstance(outputs, str):
            outputs = [outputs]
        outputs = [os.path.abspath(o) for o in outputs if isinstance(o, str)]
        if not outputs:
            continue
        if not any(o.startswith(out_dir_abs) for o in outputs):
            continue

        primary_output = outputs[0]
        start = data.get("starttime")
        end = data.get("endtime")
        duration_sec = None
        if isinstance(start, (int, float)) and isinstance(end, (int, float)) and end >= start:
            duration_sec = round(end - start, 3)

        incomplete_flag = bool(data.get("incomplete", False))
        exists_now = os.path.exists(primary_output)
        if incomplete_flag or primary_output in incomplete_outputs:
            status = "failed_or_incomplete"
        elif exists_now:
            status = "success"
        else:
            status = "missing_after_run"

        rows.append(
            {
                "rule": data.get("rule", "unknown"),
                "output": primary_output,
                "status": status,
                "duration_sec": duration_sec,
            }
        )

    return rows


def detect_run_state(log_path, overall, runtime_rows):
    if not log_path or not os.path.exists(log_path):
        return "unknown"
    with open(log_path) as handle:
        text = handle.read()
    if "Exiting because a job execution failed" in text or "Error in rule" in text:
        return "failed"
    if overall["total"] > 0 and overall["finished"] == overall["total"] and overall["failed_or_incomplete"] == 0 and overall["missing"] == 0:
        return "success"
    if runtime_rows:
        return "running"
    return "unknown"


def build_live_status(out_dir, snakemake_dir, final_status_json=None):
    runtime_rows = collect_runtime_rows(snakemake_dir, out_dir)
    latest_log = latest_snakemake_log(os.path.join(snakemake_dir, "log"))
    job_totals = parse_job_stats_table(latest_log)

    counts = defaultdict(lambda: {"finished": 0, "failed_or_incomplete": 0, "missing": 0})
    for row in runtime_rows:
        rule = row["rule"]
        if row["status"] == "success":
            counts[rule]["finished"] += 1
        elif row["status"] == "failed_or_incomplete":
            counts[rule]["failed_or_incomplete"] += 1
        else:
            counts[rule]["missing"] += 1

    all_rules = sorted(set(job_totals) | set(counts))
    by_job_type = []
    for rule in all_rules:
        total = job_totals.get(rule, 0)
        finished = counts[rule]["finished"]
        failed = counts[rule]["failed_or_incomplete"]
        missing = counts[rule]["missing"]
        if total == 0:
            total = finished + failed + missing
        progress = (100.0 * finished / total) if total else 0.0
        by_job_type.append(
            {
                "job_type": rule,
                "total": total,
                "finished": finished,
                "failed_or_incomplete": failed,
                "missing": missing,
                "progress_percent": round(progress, 2),
            }
        )

    overall = {
        "total": sum(x["total"] for x in by_job_type),
        "finished": sum(x["finished"] for x in by_job_type),
        "failed_or_incomplete": sum(x["failed_or_incomplete"] for x in by_job_type),
        "missing": sum(x["missing"] for x in by_job_type),
    }
    overall["progress_percent"] = round((100.0 * overall["finished"] / overall["total"]) if overall["total"] else 0.0, 2)
    overall["state"] = detect_run_state(latest_log, overall, runtime_rows)

    slowest = sorted(
        [r for r in runtime_rows if isinstance(r["duration_sec"], (int, float))],
        key=lambda x: x["duration_sec"],
        reverse=True,
    )[:10]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "out_dir": os.path.abspath(out_dir),
        "snakemake_dir": os.path.abspath(snakemake_dir),
        "latest_log": latest_log,
        "overall": overall,
        "by_job_type": by_job_type,
        "runtime_status_counts": dict(Counter(r["status"] for r in runtime_rows)),
        "slowest_jobs": slowest,
    }

    if final_status_json and os.path.exists(final_status_json):
        try:
            with open(final_status_json) as handle:
                payload["final_status_snapshot"] = json.load(handle)
        except Exception:
            payload["final_status_snapshot"] = {"error": f"Failed to read {final_status_json}"}

    return payload


HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ChromBPNet Status</title>
  <style>
    :root { --bg:#f3f7f4; --card:#ffffff; --ink:#1c2622; --muted:#57655f; --ok:#2f8f55; --bad:#b13a2d; --bar:#dae5de; --fill:#1f7a8c; }
    body { margin:0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; background:linear-gradient(120deg,#eef4ef,#f9fbfa); color:var(--ink); }
    .wrap { max-width:1100px; margin:20px auto; padding:0 16px; }
    .card { background:var(--card); border-radius:14px; padding:16px; box-shadow:0 6px 20px rgba(20,40,30,.08); margin-bottom:14px; }
    .top { display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }
    .state { font-weight:700; padding:4px 10px; border-radius:999px; background:#e4efe8; }
    .state.failed { background:#f7e5e3; color:var(--bad); }
    .state.success { background:#e3f2e9; color:var(--ok); }
    .progress { height:12px; border-radius:999px; background:var(--bar); overflow:hidden; }
    .fill { height:100%; background:linear-gradient(90deg,#2b8aa6,#1b6377); }
    table { width:100%; border-collapse:collapse; font-size:14px; }
    th, td { text-align:left; border-bottom:1px solid #e8efea; padding:8px 6px; }
    .muted { color:var(--muted); font-size:13px; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="top">
        <div>
          <h2 style="margin:0 0 6px 0;">ChromBPNet Pipeline Status</h2>
          <div class="muted" id="meta"></div>
        </div>
        <div id="state" class="state">unknown</div>
      </div>
      <div style="margin-top:12px;" class="progress"><div id="overallFill" class="fill" style="width:0%;"></div></div>
      <div class="muted" style="margin-top:8px;" id="overallText"></div>
    </div>
    <div class="card">
      <h3 style="margin-top:0;">Progress by Job Type</h3>
      <table>
        <thead><tr><th>Job Type</th><th>Progress</th><th>Finished</th><th>Failed</th><th>Missing</th><th>Total</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
    <div class="card">
      <h3 style="margin-top:0;">Top Slowest Jobs</h3>
      <table>
        <thead><tr><th>Rule</th><th>Duration (sec)</th><th>Output</th></tr></thead>
        <tbody id="slowRows"></tbody>
      </table>
    </div>
  </div>
  <script>
    const REFRESH_SECONDS = {{ refresh_seconds }};
    async function loadStatus() {
      const r = await fetch('/api/status');
      const d = await r.json();
      document.getElementById('meta').textContent = `Updated ${d.generated_at} | log: ${d.latest_log || 'n/a'}`;
      const state = document.getElementById('state');
      state.textContent = d.overall.state;
      state.className = `state ${d.overall.state}`;
      document.getElementById('overallFill').style.width = `${d.overall.progress_percent}%`;
      document.getElementById('overallText').textContent =
        `${d.overall.finished}/${d.overall.total} finished, ${d.overall.failed_or_incomplete} failed, ${d.overall.missing} missing (${d.overall.progress_percent}%)`;
      const rows = document.getElementById('rows');
      rows.innerHTML = '';
      for (const row of d.by_job_type) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${row.job_type}</td><td>${row.progress_percent}%</td><td>${row.finished}</td><td>${row.failed_or_incomplete}</td><td>${row.missing}</td><td>${row.total}</td>`;
        rows.appendChild(tr);
      }
      const slowRows = document.getElementById('slowRows');
      slowRows.innerHTML = '';
      for (const row of (d.slowest_jobs || [])) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${row.rule}</td><td>${row.duration_sec ?? ''}</td><td>${row.output}</td>`;
        slowRows.appendChild(tr);
      }
    }
    loadStatus();
    setInterval(loadStatus, REFRESH_SECONDS * 1000);
  </script>
</body>
</html>
"""


def build_app(out_dir, snakemake_dir, refresh_seconds, final_status_json):
    app = Flask(__name__)

    @app.get("/healthz")
    def health():
        return {"ok": True}

    @app.get("/api/status")
    def api_status():
        return jsonify(build_live_status(out_dir=out_dir, snakemake_dir=snakemake_dir, final_status_json=final_status_json))

    @app.get("/")
    def index():
        return render_template_string(HTML, refresh_seconds=refresh_seconds)

    return app


def main():
    parser = argparse.ArgumentParser(description="Run ChromBPNet status dashboard server.")
    parser.add_argument("--out-dir", required=True, help="Pipeline output directory.")
    parser.add_argument("--snakemake-dir", required=True, help="Snakemake runtime directory (usually workflow/.snakemake).")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--refresh-seconds", type=int, default=30)
    parser.add_argument("--final-status-json", default=None, help="Optional final status snapshot path.")
    args = parser.parse_args()

    app = build_app(
        out_dir=args.out_dir,
        snakemake_dir=args.snakemake_dir,
        refresh_seconds=args.refresh_seconds,
        final_status_json=args.final_status_json,
    )
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()

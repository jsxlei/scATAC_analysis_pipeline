#!/usr/bin/env python3
"""Generate latest-only summary report and status snapshot for ChromBPNet outputs."""

import argparse
import base64
import csv
import datetime as dt
import gzip
import json
import os
from collections import Counter


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def split_csv(value):
    if not value:
        return []
    return [x.strip() for x in str(value).split(",") if x.strip()]


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def bytes_human(num_bytes):
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0 or unit == "TB":
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def count_lines(path):
    if not os.path.exists(path):
        return None
    if path.endswith(".gz"):
        with gzip.open(path, "rt") as handle:
            return sum(1 for _ in handle)
    with open(path) as handle:
        return sum(1 for _ in handle)


def count_peak_bp(path):
    if not os.path.exists(path):
        return None
    total = 0
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            try:
                start = int(parts[1])
                end = int(parts[2])
            except ValueError:
                continue
            total += max(0, end - start)
    return total


def decode_metadata_path_name(encoded):
    pad_len = (-len(encoded)) % 4
    padded = encoded + ("=" * pad_len)
    try:
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
    except Exception:
        return None


def collect_incomplete_outputs(snakemake_dir, out_dir):
    incomplete_dir = os.path.join(snakemake_dir, "incomplete")
    out_dir_abs = os.path.abspath(out_dir)
    incomplete_outputs = set()
    if not os.path.isdir(incomplete_dir):
        return incomplete_outputs

    for name in os.listdir(incomplete_dir):
        decoded = decode_metadata_path_name(name)
        if decoded and os.path.abspath(decoded).startswith(out_dir_abs):
            incomplete_outputs.add(os.path.abspath(decoded))
    return incomplete_outputs


def collect_runtime_rows(snakemake_dir, out_dir):
    metadata_dir = os.path.join(snakemake_dir, "metadata")
    out_dir_abs = os.path.abspath(out_dir)
    rows = []
    incomplete_outputs = collect_incomplete_outputs(snakemake_dir, out_dir)
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
                "start_time_unix": start if start is not None else "",
                "end_time_unix": end if end is not None else "",
                "duration_sec": duration_sec if duration_sec is not None else "",
                "status": status,
            }
        )

    rows.sort(key=lambda r: (str(r["rule"]), str(r["output"])))
    return rows


def selected_peak_paths(celltypes, peak_dir, peak_suffix, union_peak, use_union_peaks):
    if use_union_peaks:
        return {ct: union_peak for ct in celltypes}
    return {ct: os.path.join(peak_dir, f"{ct}{peak_suffix}") for ct in celltypes}


def write_tsv(path, fieldnames, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def build_job_progress(job_type_to_files, runtime_rows):
    runtime_by_output = {os.path.abspath(r["output"]): r["status"] for r in runtime_rows}
    rows = []
    for job_type in sorted(job_type_to_files):
        files = list(dict.fromkeys(job_type_to_files[job_type]))
        total = len(files)
        finished = 0
        failed = 0
        missing = 0
        for path in files:
            apath = os.path.abspath(path)
            runtime_status = runtime_by_output.get(apath)
            exists = os.path.exists(apath)
            if runtime_status == "failed_or_incomplete":
                failed += 1
            elif exists:
                finished += 1
            else:
                missing += 1
        progress = (100.0 * finished / total) if total else 0.0
        rows.append(
            {
                "job_type": job_type,
                "total": total,
                "finished": finished,
                "failed_or_incomplete": failed,
                "missing": missing,
                "progress_percent": round(progress, 2),
            }
        )

    overall_total = sum(x["total"] for x in rows)
    overall_finished = sum(x["finished"] for x in rows)
    overall_failed = sum(x["failed_or_incomplete"] for x in rows)
    overall_missing = sum(x["missing"] for x in rows)
    overall_progress = (100.0 * overall_finished / overall_total) if overall_total else 0.0
    state = "failed" if (overall_failed > 0 or overall_missing > 0) else "success"
    return {
        "by_job_type": rows,
        "overall": {
            "total": overall_total,
            "finished": overall_finished,
            "failed_or_incomplete": overall_failed,
            "missing": overall_missing,
            "progress_percent": round(overall_progress, 2),
            "state": state,
        },
    }


def write_status_markdown(path, status_data):
    overall = status_data["overall"]
    with open(path, "w") as out:
        out.write("# ChromBPNet Status\n\n")
        out.write(f"- Generated: `{status_data['generated_at']}`\n")
        out.write(f"- State: `{overall['state']}`\n")
        out.write(f"- Finished jobs: `{overall['finished']}/{overall['total']}`\n")
        out.write(f"- Failed/incomplete: `{overall['failed_or_incomplete']}`\n")
        out.write(f"- Missing: `{overall['missing']}`\n\n")
        out.write("## Progress by Job Type\n\n")
        out.write("| Job type | Finished | Failed/Incomplete | Missing | Total | Progress % |\n")
        out.write("|---|---:|---:|---:|---:|---:|\n")
        for row in status_data["by_job_type"]:
            out.write(
                f"| {row['job_type']} | {row['finished']} | {row['failed_or_incomplete']} | "
                f"{row['missing']} | {row['total']} | {row['progress_percent']} |\n"
            )


def make_markdown(
    md_path,
    now_iso,
    use_union_peaks,
    out_dir,
    report_dir,
    file_rows,
    peak_rows,
    runtime_rows,
):
    missing_files = [r for r in file_rows if r["exists"] == 0]
    zero_byte = [r for r in file_rows if r["exists"] == 1 and r["size_bytes"] == 0]
    total_size = sum(r["size_bytes"] for r in file_rows if r["exists"] == 1)
    runtime_by_status = Counter(r["status"] for r in runtime_rows)
    failed_runtime_rows = [r for r in runtime_rows if r["status"] != "success"]
    slowest = sorted(
        [r for r in runtime_rows if isinstance(r["duration_sec"], (int, float))],
        key=lambda r: r["duration_sec"],
        reverse=True,
    )[:10]
    file_type_counts = Counter()
    for r in file_rows:
        if r["exists"] != 1:
            continue
        if r["path"].endswith(".bed.gz"):
            ext = ".bed.gz"
        else:
            ext = os.path.splitext(r["path"])[1] or "<no_ext>"
        file_type_counts[ext] += 1
    largest = sorted([r for r in file_rows if r["exists"] == 1], key=lambda r: r["size_bytes"], reverse=True)[:10]

    with open(md_path, "w") as out:
        out.write("# ChromBPNet Pipeline Summary Report\n\n")
        out.write(f"- Generated: `{now_iso}`\n")
        out.write(f"- Output dir: `{out_dir}`\n")
        out.write(f"- Report dir: `{report_dir}`\n")
        out.write(f"- Peak mode: `{'union_peak' if use_union_peaks else 'cell_type_resolved_peak'}`\n\n")
        out.write("## Completion Summary\n\n")
        out.write(f"- Expected files tracked: `{len(file_rows)}`\n")
        out.write(f"- Existing files: `{len(file_rows) - len(missing_files)}`\n")
        out.write(f"- Missing files: `{len(missing_files)}`\n")
        out.write(f"- Zero-byte files: `{len(zero_byte)}`\n")
        out.write(f"- Total size (existing tracked files): `{bytes_human(total_size)}`\n\n")
        out.write("## Runtime Summary\n\n")
        out.write(f"- Runtime records found: `{len(runtime_rows)}`\n")
        out.write(f"- Success: `{runtime_by_status.get('success', 0)}`\n")
        out.write(f"- Failed/Incomplete: `{runtime_by_status.get('failed_or_incomplete', 0)}`\n")
        out.write(f"- Missing-after-run: `{runtime_by_status.get('missing_after_run', 0)}`\n\n")
        out.write("## Peak Stats\n\n")
        out.write("| Cell type | Peak file | Exists | Regions | Total bp |\n")
        out.write("|---|---|---:|---:|---:|\n")
        for row in peak_rows:
            out.write(f"| {row['cell_type']} | `{row['peak_file']}` | {row['exists']} | {row['region_count']} | {row['total_bp']} |\n")
        out.write("\n")
        out.write("## Existing File Types\n\n")
        out.write("| Extension | Count |\n")
        out.write("|---|---:|\n")
        for ext, count in sorted(file_type_counts.items(), key=lambda kv: kv[0]):
            out.write(f"| `{ext}` | {count} |\n")
        out.write("\n")
        out.write("## Top 10 Largest Files\n\n")
        out.write("| Path | Size |\n")
        out.write("|---|---:|\n")
        for row in largest:
            out.write(f"| `{row['path']}` | {row['size_human']} |\n")
        out.write("\n")
        out.write("## Top 10 Slowest Runtime Entries\n\n")
        out.write("| Rule | Duration (sec) | Output |\n")
        out.write("|---|---:|---|\n")
        for row in slowest:
            out.write(f"| {row['rule']} | {row['duration_sec']} | `{row['output']}` |\n")
        out.write("\n")
        out.write("## Missing Files\n\n")
        if missing_files:
            for row in missing_files:
                out.write(f"- `{row['path']}`\n")
        else:
            out.write("- None\n")
        out.write("\n")
        out.write("## Failed/Incomplete Runtime Entries\n\n")
        if failed_runtime_rows:
            for row in failed_runtime_rows[:200]:
                out.write(f"- `{row['rule']}` `{row['status']}` `{row['output']}`\n")
            if len(failed_runtime_rows) > 200:
                out.write(f"- ... and {len(failed_runtime_rows) - 200} more\n")
        else:
            out.write("- None\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--status-dir", required=True)
    parser.add_argument("--peak-dir", required=True)
    parser.add_argument("--peak-suffix", required=True)
    parser.add_argument("--union-peak", required=True)
    parser.add_argument("--use-union-peaks", required=True)
    parser.add_argument("--celltypes", required=True)
    parser.add_argument("--snakemake-dir", required=True)
    parser.add_argument("--job-manifest", required=True)
    parser.add_argument("--expected-files-file", default=None)
    parser.add_argument("--expected-files", nargs="*", default=[])
    args = parser.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    report_dir = os.path.abspath(args.report_dir)
    status_dir = os.path.abspath(args.status_dir)
    ensure_dir(report_dir)
    ensure_dir(status_dir)

    celltypes = split_csv(args.celltypes)
    use_union_peaks = parse_bool(args.use_union_peaks)
    expected_files = list(dict.fromkeys(args.expected_files))
    if args.expected_files_file:
        with open(args.expected_files_file) as handle:
            expected_files = json.load(handle)

    with open(args.job_manifest) as handle:
        job_type_to_files = json.load(handle)

    file_rows = []
    for path in expected_files:
        exists = os.path.exists(path)
        size_bytes = os.path.getsize(path) if exists else 0
        file_rows.append(
            {
                "path": path,
                "exists": 1 if exists else 0,
                "size_bytes": size_bytes,
                "size_human": bytes_human(size_bytes),
                "line_count": count_lines(path) if exists and (path.endswith(".bed") or path.endswith(".bed.gz") or path.endswith(".tsv")) else "",
            }
        )

    peaks = selected_peak_paths(celltypes=celltypes, peak_dir=args.peak_dir, peak_suffix=args.peak_suffix, union_peak=args.union_peak, use_union_peaks=use_union_peaks)
    peak_rows = []
    for ct, path in peaks.items():
        exists = os.path.exists(path)
        size_bytes = os.path.getsize(path) if exists else 0
        peak_rows.append(
            {
                "cell_type": ct,
                "peak_file": path,
                "use_union_peaks": "true" if use_union_peaks else "false",
                "exists": 1 if exists else 0,
                "size_bytes": size_bytes,
                "size_human": bytes_human(size_bytes),
                "region_count": count_lines(path) if exists else "",
                "total_bp": count_peak_bp(path) if exists else "",
            }
        )

    runtime_rows = collect_runtime_rows(args.snakemake_dir, out_dir)

    file_stats_tsv = os.path.join(report_dir, "file_stats.tsv")
    peak_stats_tsv = os.path.join(report_dir, "peak_stats.tsv")
    runtime_stats_tsv = os.path.join(report_dir, "runtime_stats.tsv")
    summary_json = os.path.join(report_dir, "summary.json")
    summary_md = os.path.join(report_dir, "summary.md")
    status_json = os.path.join(status_dir, "status.json")
    status_md = os.path.join(status_dir, "status.md")

    write_tsv(file_stats_tsv, ["path", "exists", "size_bytes", "size_human", "line_count"], file_rows)
    write_tsv(peak_stats_tsv, ["cell_type", "peak_file", "use_union_peaks", "exists", "size_bytes", "size_human", "region_count", "total_bp"], peak_rows)
    write_tsv(runtime_stats_tsv, ["rule", "output", "start_time_unix", "end_time_unix", "duration_sec", "status"], runtime_rows)

    now_iso = dt.datetime.now().isoformat(timespec="seconds")
    summary = {
        "generated_at": now_iso,
        "out_dir": out_dir,
        "report_dir": report_dir,
        "use_union_peaks": use_union_peaks,
        "num_celltypes": len(celltypes),
        "num_expected_files": len(file_rows),
        "num_existing_files": sum(1 for r in file_rows if r["exists"] == 1),
        "num_missing_files": sum(1 for r in file_rows if r["exists"] == 0),
        "num_zero_byte_files": sum(1 for r in file_rows if r["exists"] == 1 and r["size_bytes"] == 0),
        "total_size_bytes_existing_files": sum(r["size_bytes"] for r in file_rows if r["exists"] == 1),
        "runtime_status_counts": dict(Counter(r["status"] for r in runtime_rows)),
        "runtime_rule_counts": dict(Counter(r["rule"] for r in runtime_rows)),
        "outputs": {
            "summary_md": summary_md,
            "summary_json": summary_json,
            "file_stats_tsv": file_stats_tsv,
            "peak_stats_tsv": peak_stats_tsv,
            "runtime_stats_tsv": runtime_stats_tsv,
        },
    }
    with open(summary_json, "w") as out:
        json.dump(summary, out, indent=2, sort_keys=True)

    make_markdown(summary_md, now_iso, use_union_peaks, out_dir, report_dir, file_rows, peak_rows, runtime_rows)

    status_data = build_job_progress(job_type_to_files=job_type_to_files, runtime_rows=runtime_rows)
    status_data.update(
        {
            "generated_at": now_iso,
            "out_dir": out_dir,
            "report_dir": report_dir,
            "status_dir": status_dir,
            "summary_md": summary_md,
            "summary_json": summary_json,
            "runtime_stats_tsv": runtime_stats_tsv,
        }
    )
    with open(status_json, "w") as out:
        json.dump(status_data, out, indent=2, sort_keys=True)
    write_status_markdown(status_md, status_data)


if __name__ == "__main__":
    main()

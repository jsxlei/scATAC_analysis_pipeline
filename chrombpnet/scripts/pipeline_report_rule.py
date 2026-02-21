#!/usr/bin/env python3
"""Snakemake script entrypoint for report_pipeline rule."""

import json
import os
import subprocess
import sys


job_type_to_files = {
    "average_shap": list(snakemake.input.average_shap),
    "modisco": list(snakemake.input.modisco),
    "hitcaller": list(snakemake.input.hitcaller),
    "prediction": list(snakemake.input.predictions),
    "train": list(snakemake.input.models),
    "negatives": list(snakemake.input.negatives),
}
expected_files = list(dict.fromkeys(sum(job_type_to_files.values(), [])))

status_dir = snakemake.params.status_dir
os.makedirs(status_dir, exist_ok=True)
manifest_path = os.path.join(status_dir, "job_manifest.json")
expected_files_path = os.path.join(status_dir, "expected_files.json")

with open(manifest_path, "w") as handle:
    json.dump(job_type_to_files, handle, indent=2, sort_keys=True)
with open(expected_files_path, "w") as handle:
    json.dump(expected_files, handle, indent=2)

report_script = os.path.join(snakemake.scriptdir, "pipeline_report_v2.py")
cmd = [
    sys.executable,
    report_script,
    "--out-dir",
    snakemake.params.out_dir,
    "--report-dir",
    snakemake.params.report_dir,
    "--status-dir",
    snakemake.params.status_dir,
    "--peak-dir",
    snakemake.params.peak_dir,
    "--peak-suffix",
    snakemake.params.peak_suffix,
    "--union-peak",
    snakemake.params.union_peak,
    "--use-union-peaks",
    str(snakemake.params.use_union_peaks),
    "--celltypes",
    snakemake.params.celltypes,
    "--snakemake-dir",
    snakemake.params.snakemake_dir,
    "--job-manifest",
    manifest_path,
    "--expected-files-file",
    expected_files_path,
]
subprocess.run(cmd, check=True)

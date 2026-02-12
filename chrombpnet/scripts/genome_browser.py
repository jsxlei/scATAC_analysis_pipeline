"""
Create WashU Epigenome Browser datahub JSON for ChromBPNet pipeline outputs.

Discovers cell types from the bigwig input directory and generates tracks for:
  - Training data bigwigs       (inputs/4_bigwig/)
  - Peaks                       (inputs/3_peaks/)
  - ChromBPNet predictions       (output/predictions/ — nobias and bias-included)
  - DeepSHAP contribution scores (output/shap/ — per head, averaged across folds)
  - Motif hit calls              (output/hitcaller/ — per head)

Usage:
    python scripts/make_datahub.py \
        --path /oak/stanford/groups/akundaje/leixiong/projects/<project>/results/2_chrombpnet

    python scripts/make_datahub.py \
        --path /oak/stanford/groups/akundaje/leixiong/projects/<project>/results/2_chrombpnet \
        --outdir /custom/output \
        --heads counts \
        --peak_suffix _peaks.narrowPeak

Arguments:
    --path          Path to the pipeline results directory (required)
    --outdir        Output directory for datahub.json (default: {path}/datahub/)
    --peak_suffix   Peak file suffix (default: _peaks_overlap_filtered.narrowPeak)
    --heads         SHAP/hitcaller heads to include (default: counts profile)

Expected directory structure under --path:
    inputs/
        4_bigwig/{celltype}_unstranded.bw
        3_peaks/{celltype}{peak_suffix}
    output/
        predictions/{celltype}/pred_chrombpnet_nobias.bw
        predictions/{celltype}/pred_chrombpnet.bw
        shap/{celltype}/average.{head}.bw
        hitcaller/{celltype}/{head}/hits.bed.gz
"""

import json
import os
import subprocess
import argparse

# Parse the arguments
parser = argparse.ArgumentParser(description='Create datahub files for the outputs of the pipeline')
parser.add_argument('--path', type=str, help='Path to the pipeline results directory')
parser.add_argument('--outdir', type=str, default=None, help='Output directory for the datahub files')
parser.add_argument('--peak_suffix', type=str, default='_peaks_overlap_filtered.narrowPeak',
                    help='Peak file suffix')
parser.add_argument('--heads', type=str, nargs='+', default=['counts'], #, 'profile'],
                    help='SHAP/hitcaller heads to include')

args = parser.parse_args()

bigwig_path = os.path.join(args.path, 'inputs', '4_bigwig')

# List of names
names = sorted([i.replace('_unstranded.bw', '') for i in os.listdir(bigwig_path)])
url = "https://mitra.stanford.edu/kundaje/oak/leixiong/"
url_path = url + args.path.replace('/users/leixiong', '')

# URL templates for all output types
# Inputs
bigwig_url = os.path.join(url_path, "inputs/4_bigwig/{name}_unstranded.bw")
peaks_url = os.path.join(url_path, "inputs/3_peaks/{name}{peak_suffix}.gz")

# Predictions
prediction_nobias_url = os.path.join(url_path, "output/predictions/{name}/pred_chrombpnet_nobias.bw")
prediction_full_url = os.path.join(url_path, "output/predictions/{name}/pred_chrombpnet.bw")

# SHAP and hitcaller (parameterized by head)
shap_url = os.path.join(url_path, "output/shap/{name}/average.{head}.bw")
hits_url = os.path.join(url_path, "output/hitcaller/{name}/{head}/hits.bed.gz")

# Output directory
if args.outdir is None:
    args.outdir = os.path.join(args.path, 'datahub')
os.makedirs(args.outdir, exist_ok=True)

# bgzip and tabix-index peak files if .gz/.tbi don't already exist
peaks_dir = os.path.join(args.path, 'inputs', '3_peaks')
for name in names:
    peak_file = os.path.join(peaks_dir, f"{name}{args.peak_suffix}")
    peak_gz = peak_file + ".gz"
    peak_tbi = peak_gz + ".tbi"
    if not os.path.exists(peak_gz) and os.path.exists(peak_file):
        print(f"bgzip: {peak_file}")
        subprocess.run(f"bgzip -c {peak_file} > {peak_gz}", shell=True, check=True)
    if not os.path.exists(peak_tbi) and os.path.exists(peak_gz):
        print(f"tabix: {peak_gz}")
        subprocess.run(["tabix", "-p", "bed", peak_gz], check=True)

# Generate browser tracks in WashU data hub format
tracks = []

for name in names:
    # Training data bigwig
    tracks.append({
        "type": "bigwig",
        "url": bigwig_url.format(name=name),
        "name": f"{name} Training",
        "showOnHubLoad": False,
        "options": {
            "aggregateMethod": "MAX",
            "color": "black",
        },
        "metadata": {
            "cluster": name,
            "content": "training_bw",
        },
    })

    # Peaks
    tracks.append({
        "type": "bed",
        "url": peaks_url.format(name=name, peak_suffix=args.peak_suffix),
        "name": f"{name} Peaks",
        "showOnHubLoad": False,
        "options": {
            "aggregateMethod": "MAX",
        },
        "metadata": {
            "cluster": name,
            "content": "peaks",
        },
    })

    # Chrombpnet predictions (no bias)
    tracks.append({
        "type": "bigwig",
        "url": prediction_nobias_url.format(name=name),
        "name": f"{name} Chrombpnet Predictions",
        "showOnHubLoad": False,
        "options": {
            "aggregateMethod": "MAX",
        },
        "metadata": {
            "cluster": name,
            "content": "predictions",
        },
    })

    # Chrombpnet predictions (bias-included)
    tracks.append({
        "type": "bigwig",
        "url": prediction_full_url.format(name=name),
        "name": f"{name} Bias-Included Chrombpnet Predictions",
        "showOnHubLoad": False,
        "options": {
            "aggregateMethod": "MAX",
        },
        "metadata": {
            "cluster": name,
            "content": "predictions_withbias",
        },
    })

    # SHAP and hitcaller tracks for each head
    for head in args.heads:
        # SHAP contribution scores
        tracks.append({
            "type": "dynseq",
            "url": shap_url.format(name=name, head=head),
            "name": f"{name} {head.capitalize()} DeepSHAPs",
            "showOnHubLoad": False,
            "options": {
                "aggregateMethod": "MAX",
            },
            "metadata": {
                "cluster": name,
                "content": f"{head}_shap",
            },
        })

        # Motif hit calls
        tracks.append({
            "type": "bed",
            "url": hits_url.format(name=name, head=head),
            "name": f"{name} {head.capitalize()} Motif Hit Calls",
            "showOnHubLoad": False,
            "options": {
                "aggregateMethod": "MAX",
                "alwaysDrawLabel": True,
            },
            "metadata": {
                "cluster": name,
                "content": f"{head}_hits",
            },
        })

# Save datahub to a single JSON file
datahub_file = os.path.join(args.outdir, 'datahub.json')
with open(datahub_file, "w") as f:
    json.dump(tracks, f, indent=4)

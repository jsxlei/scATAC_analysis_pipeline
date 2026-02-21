# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Snakemake-based bioinformatics pipeline for single-cell ATAC-seq analysis using ChromBPNet (deep learning model for chromatin accessibility). Two-stage pipeline: **preprocessing** (fragment processing → peak calling → bigwigs) and **chrombpnet** (model training → SHAP scores → motif discovery → hit calling → variant scoring).

## Architecture

### Two-Stage Design

**Stage 1 — `preprocessing/`**: Fragment files → cell-type-level peaks and bigwigs
```
zcat → extract_sample_fragments (C++ binary) → group_celltype → callpeak (MACS2) → make_union_peak
                                                                                  → make_bigwig
```

**Stage 2 — `chrombpnet/`**: Peaks + fragments → trained models → interpretability outputs
```
negatives → train (GPU) → shap (GPU) → average_shap → h5_to_bw → modisco → report_modisco → hitcaller (GPU)
                                                                                            → make_datahub
                          prediction (GPU)
                          pipeline_report
```

**`variant_scoring/`**: Standalone Python scripts (not Snakemake) for post-hoc variant effect analysis.

### Cell Type Discovery

ChromBPNet Snakefile auto-discovers cell types from `peak_dir` files matching `{cell_type}{peak_suffix}`. Supports override via `cell_type` (single), `cell_types` (list), `cell_types_file`, or `cell_type_index`/`cell_type_index_file` for subsetting.

### Key Patterns

- **Shell prefix**: All shell rules source `scripts/env_setup.sh` for CUDA setup via `shell.prefix()`
- **Idempotent rules**: Most rules check if output exists before running
- **Disk cleanup**: `average_shap` deletes per-fold SHAP files after averaging
- **Dynamic memory**: `shap` rule calculates memory as `peak_count / 5000` GB
- **GPU rules**: `train`, `shap`, `hitcaller`, `prediction` require GPUs (`resources: gpu=1`)
- **Config layering**: `config.yaml` defaults, overrideable via `--config key=value` CLI
- **Conda env by name**: Rules reference `conda: "chrombpnet"` (pre-installed env name, not YAML path)
- **Report uses `script:` directive**: `pipeline_report.smk` calls `pipeline_report_rule.py` → delegates to `pipeline_report_v2.py` via subprocess

## Running the Pipeline

Requires Snakemake 7.x. Two conda environments: `callpeak` (preprocessing) and `chrombpnet` (main pipeline).

```bash
# Preprocessing
cd preprocessing
snakemake -j 30 --profile profiles/cls --configfile config.yaml

# ChromBPNet (SLURM cluster)
cd chrombpnet
snakemake -j 40 --profile profiles/cls --configfile config.yaml

# Single cell type override
snakemake -j 10 --profile profiles/cls --config cell_type=Macrophage

# Local execution
snakemake -c 1 --profile profiles/local
```

### Live Status Dashboard

```bash
python scripts/status_server.py --out-dir <out_dir> --snakemake-dir .snakemake --port 8787
```

## SLURM Profiles

- `profiles/cls/config.yaml` — sbatch command template
- `profiles/cls/cls.yaml` — per-rule resource specs (partition, GPU, memory, time)

GPU rules run on `akundaje` partition; CPU rules on `akundaje,owners,normal`.

## Configuration

Both stages use `config.yaml` with paths to:
- `peak_dir`, `input_dir`, `out_dir` — input/output directories
- `genome_build` (hg38/mm10), `genome_dir` — reference genome with `.fa`, `.chrom.sizes`, `blacklist.bed.gz`, `bias.h5`, `splits/fold_*.json`
- `motif_dir` — motif database (`all.dbs.meme`, `motif_to_pwm.tsv`, `metadata.tsv`)
- `email` block — optional email notifications on pipeline completion/failure

Important config notes:
- No trailing `/` on directory paths
- Preprocessing barcode files must be named `{sample}-{celltype}.txt` (no `-` in cell type names)
- `format: frag` or `format: bam` controls input type for chrombpnet stage

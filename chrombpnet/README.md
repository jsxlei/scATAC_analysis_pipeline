# ChromBPNet pipeline

## Pipeline
- Train model with union peaks and union negatives
- Get shap value (contribution score)
- Average shap value
- deep MoDISco run with 1M seqlets on averaged shaps
- predict in union peak regions across folds and average to generate bw
- call hits for motifs from each cell type
- make session file (datahub) for WashU genome browser

## Prerequirements
1. Enviroments
    - snakemake (version=7*)
    - chrombpnet
    - finemo_gpu
    
2. Genome data      
    Download from here

3. Define input and output in the config.yaml file      
```
peak_dir: "path to folder of narrowPeak files"
peak_suffix: "suffix of narrowPeak files, peak file should named as {celltype}{peak_suffix}"
union_peak: "Union peaks or censensus peaks file across cell types, can generated in preprocessing"

input_dir: "bam path or frag path"
input_suffix: "input bam or frag should be {celltype}{input_suffix}"
format: "bam or frag"

genome_dir: "/oak/stanford/groups/akundaje/leixiong/genome"
motif_dir: "/oak/stanford/groups/akundaje/leixiong/genome/motifs"

out_dir:
```

e.g.
- peak_dir
    - celltypeA_peaks_overlap_filtered.narrowPeak
    - celltypeB_peaks_overlap_filtered.narrowPeak
- peak_suffix = "_peaks_overlap_filtered.narrowPeak"
- input_dir
    - celltypeA_sorted.tsv
    - celltypeB_sorted.tsv
- input_suffix : "_sorted.tsv"
- format : "frag"
## Start

1. Run locally
```
snakemake -c 1 --profile profiles/local --config genome_build=mm10
```
2. Run with slurm on Clusters e.g. Sherlock at Stanford
```
snakemake -j40 --profile profiles/cls --config genome_build=mm10 
```
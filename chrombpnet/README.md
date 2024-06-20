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
peak_dir: 
peak_suffix: 
union_peak: 

input_dir: 
input_suffix: 
format: 

genome_dir: "/oak/stanford/groups/akundaje/leixiong/genome"
motif_dir: "/oak/stanford/groups/akundaje/leixiong/genome/motifs"

out_dir:
```

## Start

1. Run locally
```
    snakemake -c 1 --config genome_build=mm10 --profile profiles/local
```
2. Run with slurm on Clusters e.g. Sherlock at Stanford
```
    snakemake -j30 --config genome_build=mm10 --profile profiles/cls
```
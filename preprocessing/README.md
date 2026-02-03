# Preprocess ATAC fragment for Chrombpnet snakemake pipeline
This is a snakemake pipeline. 

# Before Start
## Installation conda environments
- create `chrombpnet` enviroment following https://github.com/kundajelab/chrombpnet   
- create `callpeak` enviroment
```
conda env create --file=envs/callpeak.yaml
```

## Custom input and output
To apply to your computer, fill in the `config.yml` file with 
- frag_dir: path to original fragment files, e.g. 
    - lane1.tsv.gz
    - lane2.tsv.gz 
- barcode_dir: path to input barcode files in the name format of sample-celltype.txt, e.g.
    - lane1-celltypeA.txt
    - lane2-celltypeA.txt
    - lane1-celltypeB.txt
    - lane2-celltypeB.txt
- out_dir
- genome_dir


## Note: 
- Split fragments file if multi samples are stored in the same file
```python scripts/utils.py --input_file fragments.tsv --out_dir frag_split```
- Make sure remove -1 suffix in the barcode in both fragment files and barcode files
- Make sure there is no `-` in celltype naming
- Do not include / at the end of the path define for dir

## Genome dir
Make genome dir in this structure:     
genome_dir
- hg38
    - fasta: "hg38.fa"
    - chrom_sizes: "hg38.chrom.sizes" # This chrom size files needs sorted by 1,10,11,...2,20,..

- mm10
    - fasta: "mm10.fa"
    - chrom_sizes: "mm10.chrom.sizes" # # This chrom size files needs sorted by 1,10,11,...2,20,..


# Start
** If on a PC or single node, -c $(nproc) is the number of cores you would like to use to run
```
snakemake -c 20 --profile profiles/local
```

** If on slurm-based cluster e.g. sherlock at Stanford
```
snakemake -j 30 --profile profiles/cls
```

** If with customized config.yaml file
```
snakemake -j 30 --profile profiles/cls --configfile config.yaml
```

## Before you run
Run a dry run with -np, e.g.
```
snakemake -c 20 --profile profiles/local
```

## Output
out_dir
- 1_sample_fragments
    - fragments
    - pseudorep1
    - pseudorep2
    - pseudorepT
- 2_celltype_fragments
    - fragments
        - {cell_type}_sorted.tsv # cell type-specific fragments 
    - pseudorep1
    - pseudorep2
    - pseudorepT
- 3_peaks
    - {cell_type}_peaks_overlap_filtered.narrowPeak # cell type-specific peaks
    - {cell type}_pval.bw
- 4_bigwig
    - {cell_type}_unstranded.bw 
- 5_union_peaks
    - union_peaks.narrowPeak

## Overvie Diagram
![](overview_diagram.png)

# Acknowledgements
Thanks Salil and Ryan for contributing the original preprocessing code.    
Please refer to https://github.com/kundajelab/scAnnot-to-chrombpnet for more details!
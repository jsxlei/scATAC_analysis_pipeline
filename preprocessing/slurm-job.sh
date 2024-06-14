#!/bin/bash
#SBATCH --job-name=igvf
#SBATCH --output=/oak/stanford/groups/akundaje/leixiong/projects/imac_igvf/2_chrombpnet/log/output_%A_%a.txt
#SBATCH --error=/oak/stanford/groups/akundaje/leixiong/projects/imac_igvf/2_chrombpnet/log/error_%A_%a.txt
#SBATCH --time=7-00:00:00
#SBATCH --ntasks=1
#SBATCH -G 1
#SBATCH --mem=60GB
#SBATCH --partition=akundaje

# Load necessary modules
module load cuda/11.2.0
module load cudnn/8.1
module load system
module load pango
module load cairo

snakemake --use-conda
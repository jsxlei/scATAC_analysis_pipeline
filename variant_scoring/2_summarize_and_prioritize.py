import pandas as pd
import numpy as np
import multiprocessing
import os
import argparse

import utils

parser = argparse.ArgumentParser()
parser.add_argument("--score_dir", type=str)
parser.add_argument("--annotated_variants_loc", "-v", type=str)
parser.add_argument("--peaks_loc", "-p", type=str, default="/users/leixiong/projects/imac_igvf/results/variants/peaks")
parser.add_argument("--prioritized_variants_loc", "-o", type=str)
args = parser.parse_args()

# tomq_human: python ~/pipeline/variant_scoring/2_summarize_and_prioritize.py --score_dir results/variants/scores/human/human_tomq -v ~/oak/genome/variants/cad_gwas_annotated.txt -o results/variants/annotations/human_tomq -p results/variants/peaks/human/
# tomq_mouse: python ~/pipeline/variant_scoring/2_summarize_and_prioritize.py --score_dir results/variants/scores/mouse/mouse_tomq -v ~/oak/genome/variants/cad_gwas_annotated.txt -o results/variants/annotations/mouse_tomq -p results/variants/peaks/human_liftover/
# imac_igvf: python ~/pipeline/variant_scoring/2_summarize_and_prioritize.py --score_dir results/variants/scores/human/imac -v ~/oak/genome/variants/cad_gwas_annotated.txt -o results/variants/annotations/imac -p results/variants/peaks/human/

# PARAMETERS
work_dir = args.score_dir #"/users/leixiong/projects/imac_igvf/results/variants/scores"
models = os.listdir(work_dir)
annotated_variants_loc = args.annotated_variants_loc #"annotated_variants.tsv"
prioritized_variants_loc = os.path.join(args.prioritized_variants_loc, "prioritized_variants.tsv")
os.makedirs(args.prioritized_variants_loc, exist_ok=True)

# CODE
print("loading variants...")
variants = pd.read_csv(annotated_variants_loc, sep="\t")

print("set up payloads...")
model_payloads = []
for model in models:
    print(f"processing {model}...")
    scores_loc = os.path.join(work_dir, model)
    peaks_loc = os.path.join(args.peaks_loc, model+'_peaks_overlap_filtered.narrowPeak')
    model_payloads.append((variants, scores_loc, peaks_loc))

print("process payloads...")
with multiprocessing.Pool(processes=32) as p:
    model_results = p.starmap(utils.prioritize_variants, model_payloads)

print("get top variants...")
for i, model in enumerate(models):
    scores_df_i = model_results[i]
    variants[f"prioritized-{model}"] = scores_df_i["prioritized"]
    variants[f"in_peak-{model}"] = scores_df_i["in_peak"]
    variants[f"LFC-{model}"] = scores_df_i["avg_logfc"]
    variants[f"score-{model}"] = (
        -np.log10(scores_df_i["gavg_abs_logfc_pval"])
        * np.sign(scores_df_i["avg_logfc"])
        * variants[f"prioritized-{model}"]
    )

print("combine top variants...")
variants["prioritized"] = variants[[f"prioritized-{model}" for model in models]].any(
    axis=1
)
variants_LFC_list = [
        pd.Series(variants[f"LFC-{m}"]*~(variants["prioritized"] & ~variants[f"prioritized-{m}"]), name=f'LFC-{m}', dtype=float) for m in models
    ]
variants_LFC = pd.concat(variants_LFC_list, axis=1)
# variants_LFC = variants[[x for x in variants.columns if x.startswith("LFC")]]
variants_LFC_abs = np.abs(variants_LFC)
most_active_model = variants_LFC_abs.idxmax(axis=1)
most_active_model_LFC = variants_LFC.apply(
    lambda row: row[most_active_model[row.name]], axis=1
)
variants["most_active_model"] = most_active_model.apply(
    lambda row: row.split("LFC-")[1]
)
variants["most_active_model_LFC"] = most_active_model_LFC

print("reorder columns...")
col_order = [
    "chr",
    "pos",
    "ref",
    "alt",
    "variant_id",
    "rsid",
    "ref_length",
    "alt_length",
    "variant_type",
]
col_order += ["prioritized", "most_active_model", "most_active_model_LFC"]
col_order += [
    "region_type",
    "gene_within_100kb",
    "nearest_gene",
    "2nd_nearest_gene",
    "3rd_nearest_gene",
]
for model in models:
    col_order += [
        f"prioritized-{model}",
        f"LFC-{model}",
        f"score-{model}",
        f"in_peak-{model}",
    ]
variants = variants[col_order]

print("saving...")
variants.to_csv(prioritized_variants_loc, sep="\t", index=False)

# e.g. python ~/pipeline/variant_scoring/2_summarize_and_prioritize.py --score_dir results/variants/scores/human/human_tomq -v ~/oak/genome/variants/cad_gwas_annotated.txt -p results/variants/peaks/ -o results/variants/annotations/human/human_tomq 
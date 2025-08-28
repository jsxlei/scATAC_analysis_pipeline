import pandas as pd
import argparse
import os
import utils

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=str)
parser.add_argument("--out_dir", type=str, default=None)
args = parser.parse_args()


# PARAMETERS
variants_loc = args.input #"/users/leixiong/oak/genome/variants/cad_gwas.txt"
# annotated_variants_loc = os.path(args.out_dir #"annotated_variants.tsv"
if args.out_dir is None:
    args.out_dir = os.path.dirname(args.input)
annotated_variants_loc = os.path.join(args.out_dir, "annotated_" + os.path.basename(args.input))
os.makedirs(args.out_dir, exist_ok=True)

# CODE
print("loading variants...")
variants = pd.read_csv(
    variants_loc, sep="\t",# names=["chr", "pos", "ref", "alt", "index"]
)
variants.columns = ["chr", "pos", "ref", "alt"] + list(variants.columns[4:])
print("annotating variants...")
variants = utils.annotate_variants(variants)
variants.to_csv(annotated_variants_loc, sep="\t", index=False)



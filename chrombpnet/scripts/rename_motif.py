import argparse
from bs4 import BeautifulSoup
import pandas as pd

parser = argparse.ArgumentParser(description='Rename motif file')
parser.add_argument('--motif_html', help='Modisco h5 file')
parser.add_argument('--motif_meta', help='Motif mapping file', default=None)
parser.add_argument('--bed', help='Hits caller bed file')
# parser.add_argument('--out', help='Output bed file', default=None)
args = parser.parse_args()

def strip_motif_name(s):
    try: 
        s.split('_')[0].split('.mouse')[0].upper()
    except:
        print(s)
        return 'NANANANANANAN'
    return s.split('_')[0].split('.mouse')[0].upper()

if args.motif_html.endswith(".html"):
    with open(args.motif_html, "r") as file:
        modisco_report = BeautifulSoup(file, "html.parser")

    table = modisco_report.find_all("table")
    df = pd.read_html(str(table))[0]
else:
    df = pd.read_csv(args.motif_html, sep="\t")

# print(df)

if args.motif_meta:
    meta = pd.read_csv(args.motif_meta, sep="\t")
    # df = pd.merge(df, meta, left_on='match0', right_on='motif_id', how='left')
    motif_id_dict = pd.Series(meta['tf_name'].values, meta['motif_id'].values).to_dict()
    source_id_dict = pd.Series(meta['tf_name'].values, meta['source_id'].values).to_dict()
    mapping_dict = {}
    for i, row in df.iterrows():
        # print(row)
        k = row.loc['pattern']
        v = row.loc['match0']
        if v in motif_id_dict:
            mapping_dict[k] = motif_id_dict[v]            
        elif v in source_id_dict:
            mapping_dict[k] = source_id_dict[v]
        else:
            print(f"{k} {v} Not found")
    # mapping_dict = pd.Series(df['tf_name'].values, df['pattern'].values).to_dict()
    # import pdb; pdb.set_trace()
else:
    mapping_dict = pd.Series(df['match0'].values, df['pattern'].values).to_dict()
# print(mapping_dict)


hits = pd.read_csv(args.bed, sep="\t") #, header=None)
# hits.columns = ["chrom", "start", "end", "pattern", "score", "strand"]

# hits['pattern'] = hits['pattern'].map(mapping_dict) #.apply(strip_motif_name)
hits['pattern'] = hits['motif_name'].map(mapping_dict) #.apply(strip_motif_name)
hits = hits[['chr', 'start', 'end', 'pattern', 'hit_coefficient', 'strand']]
# print(hits.head())

hits.dropna(subset=['pattern'], inplace=True)
hits.drop_duplicates(inplace=True, subset=['chr', 'start', 'end', 'pattern'])
# print(hits.head())
if args.bed.endswith(".tsv"):
    args.bed = args.bed.replace(".tsv", ".bed")
# print(args.bed)
hits.to_csv(args.bed, sep="\t", header=None, index=None) #, compression='bgzip')


import os

# # Load the module
os.system("module load biology samtools")
# # Run bgzip and tabix commands
os.system(f"bgzip -c {args.bed} > {args.bed}.gz")
os.system(f"tabix -p bed {args.bed}.gz")


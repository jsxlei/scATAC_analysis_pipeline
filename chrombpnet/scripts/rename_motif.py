import argparse
from bs4 import BeautifulSoup
import pandas as pd

parser = argparse.ArgumentParser(description='Rename motif file')
parser.add_argument('--motif_html', help='Modisco h5 file')
parser.add_argument('--bed', help='Hits caller bed file')
args = parser.parse_args()

def strip_motif_name(s):
    try: 
        s.split('_')[0].split('.mouse')[0].upper()
    except:
        print(s)
        return 'NANANANANANAN'
    return s.split('_')[0].split('.mouse')[0].upper()

with open(args.motif_html, "r") as file:
    modisco_report = BeautifulSoup(file, "html.parser")

table = modisco_report.find_all("table")
df = pd.read_html(str(table))[0]
mapping_dict = pd.Series(df['match0'].values, df['pattern'].values).to_dict()

hits = pd.read_csv(args.bed, sep="\t", header=None)
hits.columns = ["chrom", "start", "end", "pattern", "score", "strand"]
hits['pattern'] = hits['pattern'].map(mapping_dict).apply(strip_motif_name)
hits.to_csv(args.bed, sep="\t", header=None, index=None) #, compression='bgzip')
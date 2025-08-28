import json
import os
import argparse

# Parse the arguments
parser = argparse.ArgumentParser(description='Create datahub files for the outputs of the pipeline')
parser.add_argument('--path', type=str, help='URL for the profile shap data')
parser.add_argument('--outdir', type=str, default=None, help='Output directory for the datahub files')

args = parser.parse_args()

bigwig_path = os.path.join(args.path, 'inputs', '4_bigwig')

# List of names
names = [i.replace('_unstranded.bw', '') for i in os.listdir(bigwig_path)] # results/2_chrombpnet/inputs/4_bigwig
url = "https://mitra.stanford.edu/kundaje/oak/leixiong/"
url_path  = url + args.path.replace('/users/leixiong', '')

# URLs for different types of files
profile_url_dynseq = os.path.join(url_path, 'output/shap/{name}/average.profile.bw') 
count_url_dynseq = os.path.join(url_path, 'output/shap/{name}/average.counts.bw') 
bigwig_url = os.path.join(url_path, "inputs/4_bigwig/{name}_unstranded.bw")
profile_hits_url = os.path.join(url_path, "output/hitcaller/{name}/profile/hits.bed.gz")
count_hits_url = os.path.join(url_path, "output/hitcaller/{name}/counts/hits.bed.gz")

# Output file names
if args.outdir is None:
    args.outdir = os.path.join(args.path, 'datahub')
os.makedirs(args.outdir, exist_ok=True)

profile_shap_file = os.path.join(args.outdir, 'profile_shap.json')
count_shap_file = os.path.join(args.outdir, 'count_shap.json')
bigwig_file = os.path.join(args.outdir, 'bigwig.json')
count_hits_file = os.path.join(args.outdir, 'count_hits.json')
profile_hits_file = os.path.join(args.outdir, 'profile_hits.json')


# Datahubs for different types
profile_shap_datahub = []
count_shap_datahub = []
bigwig_datahub = []
profile_hits_datahub = []
count_hits_datahub = []

# Populate the datahubs
for name in names:
    profile_entry = {
        "type": "dynseq",
        "url": profile_url_dynseq.format(name=name),
        "name": f"{name}.profile_shap",
    }
    count_entry = {
        "type": "dynseq",
        "url": count_url_dynseq.format(name=name),
        "name": f"{name}.count_shap",
    }
    bigwig_entry = {
        "type": "bigwig",
        "url": bigwig_url.format(name=name),
        "name": f"{name}_bigwig",
    }

    profile_hits_entry = {
        "type": "bed",
        "url": profile_hits_url.format(name=name),
        "name": f"{name}_hits",
    }

    count_hits_entry = {
        "type": "bed",
        "url": count_hits_url.format(name=name),
        "name": f"{name}_hits",
    }
    
    profile_shap_datahub.append(profile_entry)
    count_shap_datahub.append(count_entry)
    bigwig_datahub.append(bigwig_entry)
    profile_hits_datahub.append(profile_hits_entry)
    count_hits_datahub.append(count_hits_entry)

# Save each datahub to a separate JSON file
with open(profile_shap_file, "w") as f:
    json.dump(profile_shap_datahub, f, indent=4)

with open(count_shap_file, "w") as f:
    json.dump(count_shap_datahub, f, indent=4)

with open(bigwig_file, "w") as f:
    json.dump(bigwig_datahub, f, indent=4)

with open(profile_hits_file, "w") as f:
    json.dump(profile_hits_datahub, f, indent=4)

with open(count_hits_file, "w") as f:
    json.dump(count_hits_datahub, f, indent=4)


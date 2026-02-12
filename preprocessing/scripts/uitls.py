import os
import argparse
import numpy as np
import gzip

def split_fragment_file(input_file, out_dir='.'):
    os.makedirs(out_dir, exist_ok=True)
    # Open the input file
    if input_file.endswith('.gz'):
        f = gzip.open(input_file, 'rt')
    else:
        f = open(input_file, 'r')

    with f:
        # Initialize a dictionary to store lines for each 'n'
        fragment_dict = {}

        for line in f:
            # Assuming barcode-n is the first column in each line (modify if necessary)
            lines = line.split()
            barcode = lines[3]
            # Extract the 'n' part after the last hyphen '-'
            barcode_, n = barcode.split('-')
            lines[3] = barcode_
            # Add the line to the corresponding 'n' group
            if n not in fragment_dict:
                fragment_dict[n] = []
            line = '\t'.join(lines)+'\n'
            fragment_dict[n].append(line)

    # Write each group to a separate output file
    for n, lines in fragment_dict.items():
        output_file = os.path.join(out_dir, f"sample{n}.tsv")
        with open(output_file, 'w') as out:
            out.writelines(lines)
        print(f"Created {output_file} with {len(lines)} lines.")


def generate_barcode_file(obs, out_dir):
    """
    Generate barcode files for each fragment and cell type
    """
    obs = obs.copy()
    os.makedirs(out_dir, exist_ok=True)
    obs.index, obs['sample'] = obs.index.str.split('-').str[0], obs.index.str.split('-').str[1]
    
    # obs = adata['rna'].obs
    for frag in np.unique(obs['sample']):
        print(frag)
        for c in np.unique(obs['cell_type']):
            # print(c)
            obs[(obs['cell_type'] == c) & (obs['sample'] == frag)].index.to_frame(index=False).to_csv(
                os.path.join(out_dir, f'{frag}-{c}.txt'), header=False, index=False)

# generate_barcode_file(macro_raw['rna'].obs, barcode_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', help='Path to the input file')
    parser.add_argument('--out_dir', help='Path to the output directory', default='.')
    args = parser.parse_args()
    split_fragment_file(args.input_file, args.out_dir)

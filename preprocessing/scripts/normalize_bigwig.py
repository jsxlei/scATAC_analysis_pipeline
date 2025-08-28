#!/usr/bin/env python3
import pyBigWig
import sys
import os
import numpy as np

def normalize_bigwig(input_bw, output_bw):
    # Open input bigWig
    bw = pyBigWig.open(input_bw)

    # Get chromosome sizes
    chrom_sizes = bw.chroms()

    # Compute total signal (sum of all values)
    total_counts = 0
    for chrom, length in chrom_sizes.items():
        values = bw.values(chrom, 0, length, numpy=True)
        total_counts += np.nan_to_num(values, nan=0).sum()

    print(f"Total counts: {total_counts}")

    # Compute scaling factor
    scale = 1e6 / total_counts
    print(f"Scaling factor: {scale}")

    # Open output bigWig
    out = pyBigWig.open(output_bw, "w")
    out.addHeader(list(chrom_sizes.items()))

    # Write scaled values
    for chrom, length in chrom_sizes.items():
        # extract intervals
        intervals = bw.intervals(chrom)
        if intervals is None:
            continue
        scaled_intervals = [(start, end, value * scale) for start, end, value in intervals]
        out.addEntries([chrom]*len(scaled_intervals),
                       [s for s,_,_ in scaled_intervals],
                       ends=[e for _,e,_ in scaled_intervals],
                       values=[v for _,_,v in scaled_intervals])

    bw.close()
    out.close()
    print(f"Normalized bigWig written to {output_bw}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: normalize_bigwig.py input.bw output.cpm.bw")
        sys.exit(1)
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)
    for file in os.listdir(input_dir):
        if file.endswith(".bw"):
            input_bw = os.path.join(input_dir, file)
            output_bw = os.path.join(output_dir, file)
            normalize_bigwig(input_bw, output_bw)
    # normalize_bigwig(sys.argv[1], sys.argv[2])

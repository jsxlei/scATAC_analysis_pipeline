rule make_union_peak:
    input:
        list_peak_files
    params:
    output:
        union_peaks
    shell:
        """
        python scripts/make_consensus_peakset.py --peaks_dir {peak_dir} --output {output}
        """
    # cat {input} | sort -k1,1 -k2,2n | bedtools merge -i stdin > {output}
rule callpeak:
    input:
        list_celltype_fragment_files
    params:
        chrom_sizes = genome_config['chrom_sizes'],
        blacklist = genome_config['blacklist']
    output:
        peak_dir+"/{cell_type}"+config["peak_suffix"]
    conda:
        "callpeak"
    shell:
        """
        bash scripts/call_peaks.sh {wildcards.cell_type} {celltype_frag_dir} {peak_dir} {params.chrom_sizes} {params.blacklist}
        find {peak_dir} -name "{wildcards.cell_type}*" \
            ! -name "*_peaks_overlap_filtered.narrowPeak" \
            ! -name "*_pval.bw" \
            -delete
        """
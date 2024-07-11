rule callpeak:
    input:
        list_celltype_fragment_files
    params:
        chrom_sizes = genome_config['chrom_sizes'],
        blacklist = genome_config['blacklist']
    output:
        peak_dir+"/{cell_type}"+config["peak_suffix"]
    conda:
        "../envs/callpeak.yaml"
    shell:
        """
        bash scripts/call_peaks.sh {wildcards.cell_type} {celltype_frag_dir} {peak_dir} {params.chrom_sizes} {params.blacklist}
        """
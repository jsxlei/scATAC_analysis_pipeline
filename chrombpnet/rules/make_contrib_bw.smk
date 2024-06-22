rule make_contrib_bw:
    input:
        output_config["shap_dir"] + "/{cell_type}/average.{head}.h5",
    output:
        output_config["shap_dir"] + "/{cell_type}/average.{head}.bw",
    params:
        chrom_sizes = genome_config["chrom_sizes"],
        output_prefix = output_config["shap_dir"] + "/{cell_type}/average.{head}",
        peaks_file = config["union_peak"]    
    shell:
        """
        python3.8 scripts/importance_hdf5_to_bigwig.py \
            --hdf5 {input} \
            --regions {params.peaks_file} \
            --chrom-sizes {params.chrom_sizes} \
            --output-prefix {params.output_prefix}
        """
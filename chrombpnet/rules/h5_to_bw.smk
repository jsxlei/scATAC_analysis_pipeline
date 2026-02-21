rule h5_to_bw:
    input:
        output_config["shap_dir"] + "/{cell_type}/average.{head}.h5",
    output:
        output_config["shap_dir"] + "/{cell_type}/average.{head}.bw"
    params:
        chrom_sizes = genome_config["chrom_sizes"],
        output_prefix = output_config["shap_dir"] + "/{cell_type}/average.{head}",
        peaks_file = config["union_peak"] if USE_UNION_PEAKS else config["peak_dir"] + "/{cell_type}" + config["peak_suffix"],
        script = workflow.basedir + '/scripts/importance_hdf5_to_bigwig.py',
    conda:
        "chrombpnet"
    shell:
        """
        python {params.script} \
                --hdf5 {input} \
                --regions {params.peaks_file} \
                --chrom-sizes {params.chrom_sizes} \
                --output-prefix {params.output_prefix}
        """

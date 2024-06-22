rule prediction:
    input:
        models = expand(output_config["model_dir"] + "/{cell_type}/{fold}/models/chrombpnet_nobias.h5", cell_type=CELLTYPES, fold=config['fold']),
        peaks_file = config["union_peak"],
    output:

    params:
    conda:
        "chrombpnet"
    shell:
        """
        python scripts/predict_and_avg.py \
            {input.peaks_file} \
            {params.fasta} \
            {params.chrom_sizes} \
            {params.output_prefix} \
            {input.models}
        """
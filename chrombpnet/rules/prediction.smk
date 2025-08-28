rule prediction:
    input:
        nobias_models = expand(output_config["model_dir"] + "/{cell_type}/{fold}/models/chrombpnet_nobias.h5", cell_type=CELLTYPES, fold=config['fold']),
        full_models = expand(output_config["model_dir"] + "/{cell_type}/{fold}/models/chrombpnet.h5", cell_type=CELLTYPES, fold=config['fold']),
        peaks_file = config["union_peak"],
    output:
        ""
    params:
        fasta = genome_config["fasta"],
        chrom_sizes = genome_config["chrom_sizes"],
    conda:
        "chrombpnet"
    threads: 16
    shell:
        """
        python scripts/predict_and_average.py \
            -r {input.peaks_file} \
            -g {params.fasta} \
            -c {params.chrom_sizes} \
            -op {params.output_prefix} \
            -cm {input.nobias_models} \
            -suffix "nobias" \

        python scripts/predict_and_average.py \
            -r {input.peaks_file} \
            -g {params.fasta} \
            -c {params.chrom_sizes} \
            -op {params.output_prefix} \
            -cm {input.full_models} \
            -suffix "full" \
        """
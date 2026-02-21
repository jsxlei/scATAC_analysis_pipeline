rule prediction:
    input:
        nobias_models = expand(output_config["model_dir"] + "/{{cell_type}}/{fold}/models/chrombpnet_nobias.h5", fold=config['fold']),
        full_models = expand(output_config["model_dir"] + "/{{cell_type}}/{fold}/models/chrombpnet.h5", fold=config['fold']),
        peaks_file = config["union_peak"] if USE_UNION_PEAKS else config["peak_dir"] + "/{cell_type}" + config["peak_suffix"],
    output:
        pred_nobias = output_config["prediction_dir"] + "/{cell_type}/pred_chrombpnet_nobias.bw",
        pred = output_config["prediction_dir"] + "/{cell_type}/pred_chrombpnet.bw"
    params:
        fasta = genome_config["fasta"],
        chrom_sizes = genome_config["chrom_sizes"],
        prediction_dir = output_config["prediction_dir"],
        output_prefix = output_config["prediction_dir"]+'/{cell_type}/pred',
        script = workflow.basedir + '/scripts/predict_and_average.py',
        nobias_model_flags = lambda wildcards, input: " ".join(["-cm " + m for m in input.nobias_models]),
        full_model_flags = lambda wildcards, input: " ".join(["-cm " + m for m in input.full_models]),
    conda:
        "chrombpnet"
    threads: 16
    resources:
        gpu=1,
        mem_gb=50,

    shell:
        """
        python {params.script} \
            -r {input.peaks_file} \
            -g {params.fasta} \
            -c {params.chrom_sizes} \
            -op {params.output_prefix} \
            {params.nobias_model_flags} \
            -sfx "_nobias"

        python {params.script} \
            -r {input.peaks_file} \
            -g {params.fasta} \
            -c {params.chrom_sizes} \
            -op {params.output_prefix} \
            {params.full_model_flags} \
            -sfx ""
        """

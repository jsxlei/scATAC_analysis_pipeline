rule average_shap:
    input:
        lambda wildcards: expand(output_config["shap_dir"] + "/{cell_type}/{fold}.{head}_scores.h5", fold = config['fold'], cell_type=wildcards.cell_type,
            head=wildcards.head)
    output:
        output_config["shap_dir"] + "/{cell_type}/average.{head}.h5",
    params:
        folds = config['fold'],
        base_dir = output_config['shap_dir'] + "/{cell_type}"
    conda:
        "chrombpnet"
    resources:
        mem_gb=60
    threads: 1
    shell:
        """
        python scripts/average_shap.py \
            --shaptype {wildcards.head} \
            --base_dir {params.base_dir} \
            --folds {params.folds}
        """
rule average_shap:
    input:
        lambda wildcards: expand(output_config["shap_dir"] + "/{cell_type}/{fold}.{head}_scores.h5", 
            fold = config['fold'], cell_type=wildcards.cell_type, head=wildcards.head)
    output:
        h5 = output_config["shap_dir"] + "/{cell_type}/average.{head}.h5",
    params:
        folds = config['fold'],
        base_dir = output_config['shap_dir'] + "/{cell_type}",
        chrom_sizes = genome_config["chrom_sizes"],
        output_prefix = output_config["shap_dir"] + "/{cell_type}/average.{head}",
        peaks_file = config["union_peak"]  
    conda:
        "chrombpnet"
    resources:
        mem_gb=80
    threads: 4
    shell:
        """
        if [[ -f {output.h5} ]]; then
            echo "Found h5 files"
        else
            python scripts/average_shap.py \
                --shaptype {wildcards.head} \
                --base_dir {params.base_dir} \
                --folds {params.folds}
        fi
        """
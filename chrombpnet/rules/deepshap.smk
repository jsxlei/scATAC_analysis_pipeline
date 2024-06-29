rule deepshap:
    input:
        model = output_config["model_dir"] + "/{cell_type}/{fold}/models/chrombpnet_nobias.h5",
        union_peak = config["union_peak"],
    output: 
        shap_bw = output_config["shap_dir"] + "/{cell_type}/{fold}.{head}_scores.bw",
        shap_h5 = output_config["shap_dir"] + "/{cell_type}/{fold}.{head}_scores.h5",
    params:
        fasta = genome_config["fasta"],
        chrom_sizes = genome_config["chrom_sizes"],
        output_prefix = output_config["shap_dir"] + "/{cell_type}/{fold}",
        shap_dir = output_config["shap_dir"]
    resources:
        nvidia_gpu=1,
        mem_mb=100000
    conda:
        "chrombpnet"
    shell:
        """
        mkdir -p {params.shap_dir}

        if [[ -f {output.shap_bw} ]]; then
            echo "Found {wildcards.head} shap scores"
        else
            echo "Generate {wildcards.head} contribution score bigwigs"
            chrombpnet contribs_bw \
                -m {input.model} \
                -r {input.union_peak} \
                -g {params.fasta} \
                -c {params.chrom_sizes} \
                -op {params.output_prefix} \
                -pc {wildcards.head}
        fi
        """
rule deepshap:
    input:
        model = output_config["model_dir"] + "/{cell_type}/{fold}/models/chrombpnet_nobias.h5",
        union_peak = config["union_peak"],
    output: 
        profile_shap = output_config["shap_dir"] + "/{cell_type}/{fold}.profile_scores.bw",
        counts_shap = output_config["shap_dir"] + "/{cell_type}/{fold}.counts_scores.bw",
        profile_shap_h5 = output_config["shap_dir"] + "/{cell_type}/{fold}.profile_scores.h5",
        counts_shap_h5 = output_config["shap_dir"] + "/{cell_type}/{fold}.counts_scores.h5"
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

        if [[ -f {output.count_shap} ]]; then
            echo "Found count shap scores"
        else
            echo "Generate counts contribution score bigwigs"
            chrombpnet contribs_bw \
                -m {input.model} \
                -r {input.union_peak} \
                -g {params.fasta} \
                -c {params.chrom_sizes} \
                -op {params.output_prefix} \
                -pc counts
        fi

        if [[ -f {output.profile_shap} ]]; then
            echo "Found shape shap scores"
        else
            echo "Generate shape contribution score bigwigs"
            chrombpnet contribs_bw \
                -m {input.model} \
                -r {input.union_peak} \
                -g {params.fasta} \
                -c {params.chrom_sizes} \
                -op {params.output_prefix} \
                -pc profile
        fi


        """
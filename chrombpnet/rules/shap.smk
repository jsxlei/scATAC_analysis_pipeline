rule shap:
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
        shap_dir = output_config["shap_dir"],
        n_peaks = pd.read_csv(config['union_peak'], sep='\t').shape[0]
    resources:
        nvidia_gpu=1,
        mem_gb=lambda wildcards, attempt: params.n_peaks / 5000,  # Adjust memory based on number of samples
    conda:
        "chrombpnet"
    threads: lambda wildcards, attempt: min(4, int(params.n_peaks / 25000))
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
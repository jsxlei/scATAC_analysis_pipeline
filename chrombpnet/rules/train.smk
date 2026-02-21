# rules/train

rule train:
    input:
        input_file = config["input_dir"] + "/{cell_type}" + config['input_suffix'], 
        peaks = config['union_peak'] if USE_UNION_PEAKS else config["peak_dir"] + "/{cell_type}" + config["peak_suffix"],
        negatives = output_config["negative_dir"] + "/{cell_type}/{fold}_negatives.bed", 
        bias_model = genome_config["bias_model"],
    output:
        chrombpnet_nobias = "{model_dir}/{cell_type}/{fold}/models/chrombpnet_nobias.h5",
        full_model = "{model_dir}/{cell_type}/{fold}/models/chrombpnet.h5",
    params:
        model_dir = output_config["model_dir"],
        out_dir = output_config['model_dir'] + "/{cell_type}/{fold}",
        fasta = genome_config["fasta"],
        chrom_sizes = genome_config["chrom_sizes"],
        chr_fold = genome_config["chr_fold"],
        format = config['format']
    resources:
        gpu=1,
        mem_gb=50, 
    threads: 4
    conda:
        "chrombpnet"
    shell:
        """
        if [[ -f {output.chrombpnet_nobias} ]]; then
            echo "Found model"
        else
            if [[ -d {params.out_dir} ]]; then
                echo "Found logdir. Deleting previous model"
                rm -rf {params.out_dir}
            fi

            echo "Training model"
            chrombpnet pipeline \
                -i{params.format} {input.input_file} \
                -p {input.peaks} \
                -n {input.negatives} \
                -b {input.bias_model} \
                -o {params.out_dir} \
                -g {params.fasta} \
                -c {params.chrom_sizes} \
                -fl {params.chr_fold}/{wildcards.fold}.json \
                -d "ATAC" 
            echo "rm -r {params.out_dir}/auxiliary"
            rm -r {params.out_dir}/auxiliary
        fi
        """

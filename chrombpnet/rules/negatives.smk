# rules/negatives.smk

import os
genome_build = config["genome_build"]
genome_config = {i: os.path.join(config['genome_dir'], genome_build, config["genome"][genome_build][i]) for i in config["genome"][genome_build]}

rule negatives:
    input:
        lambda wildcards: expand("{peak_dir}/{cell_type}{peak_suffix}", 
            peak_dir=config["peak_dir"], 
            peak_suffix=config["peak_suffix"], 
            cell_type=wildcards.cell_type)
    params:
        peak_dir = config["peak_dir"],
        fasta = genome_config['fasta'],
        chrom_sizes = genome_config['chrom_sizes'], 
        chr_fold = genome_config['chr_fold'], 
        blacklist = genome_config['blacklist'], 
        fold = config["fold"],
        output_prefix = lambda wildcards: expand("{out_dir}/{negative_dir}/{cell_type}/{fold}", 
                out_dir=config["out_dir"], 
                negative_dir=config["out"]["negative_dir"], 
                cell_type=wildcards.cell_type, 
                fold=config["fold"]
            )
    output:
        "{out_dir}/{negative_dir}/{cell_type}/{fold}_negatives.bed".format(
            out_dir=config["out_dir"],
            negative_dir=config["out"]["negative_dir"],
            cell_type="{cell_type}",
            fold=config["fold"]
        )
    conda:
        "chrombpnet"
        #"../envs/chrombpnet.yaml"

    shell:
        """
        if [[ -f {output} ]];
        then
            echo "Found negatives"
        else
            echo "Preparing {output}"
            if [[ -d {params.output_prefix}_auxiliary ]];
            then
                echo "Found logdir. Deleting previous fold"
                rm -rf {params.output_prefix}_auxiliary
            fi
            chrombpnet prep nonpeaks \
                -p {input} \
                -o {params.output_prefix} \
                -g {params.fasta} \
                -c {params.chrom_sizes} \
                -fl {params.chr_fold}/{params.fold}.json \
                -br {params.blacklist}
        fi
        """
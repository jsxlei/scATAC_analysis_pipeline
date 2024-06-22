# rules/negatives.smk

rule negatives:
    input:
        peaks = config["union_peak"]
    output:
        output_config["negative_dir"] + "/{fold}_negatives.bed"
    params:
        peak_dir = config["peak_dir"],
        fasta = genome_config['fasta'],
        chrom_sizes = genome_config['chrom_sizes'], 
        chr_fold = genome_config['chr_fold'], 
        blacklist = genome_config['blacklist'],
        output_prefix = output_config["negative_dir"] + "/{fold}"
    conda:
        "chrombpnet"
    shell:
        """
        if [[ -f {output} ]]; then
            echo "Found negatives"
        else
            echo "Preparing {output}"
            if [[ -d {params.output_prefix}_auxiliary ]]; then
                echo "Found logdir. Deleting previous fold"
                rm -rf {params.output_prefix}_auxiliary
            fi
            chrombpnet prep nonpeaks \
                -p {input} \
                -o {params.output_prefix} \
                -g {params.fasta} \
                -c {params.chrom_sizes} \
                -fl {params.chr_fold}/{wildcards.fold}.json \
                -br {params.blacklist}
        fi
        """
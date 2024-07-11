rule make_bigwig:
    input:
        list_celltype_fragment_files
    params:
        chrom_sizes = genome_config['chrom_sizes'],
        fasta_file = genome_config['fasta'],
        output_prefix = bigwig_dir + "/{cell_type}"
    output:
        bigwig_dir + "/{cell_type}_unstranded.bw"
    conda:
        "chrombpnet"
    shell:
        """
        python scripts/reads_to_bigwig.py \
            -g {params.fasta_file} \
            -ifrag {celltype_frag_dir}/fragments/{wildcards.cell_type}_sorted.tsv \
            -c {params.chrom_sizes} \
            -o {params.output_prefix} \
            -d ATAC
        """
# rules/peaks.smk

rule callpeak:
    input:
        lambda wildcards: expand("{celltype_frag_dir}/fragments/{cell_type}_sorted.tsv",
                    celltype_frag_dir="{out_dir}/{celltype_fragments}".format(out_dir=config["out_dir"], celltype_fragments=config["celltype_fragments"]),
                    cell_type=wildcards.cell_type),
        # lambda wildcards: expand("{celltype_frag_dir}/pseudorep2/{cell_type}_sorted.tsv",
        #             celltype_frag_dir="{out_dir}/{celltype_fragments}".format(out_dir=config["out_dir"], celltype_fragments=config["celltype_fragments"]),
        #             cell_type=wildcards.cell_type),
        # lambda wildcards: expand("{celltype_frag_dir}/pseudorepT/{cell_type}_sorted.tsv",
        #             celltype_frag_dir="{out_dir}/{celltype_fragments}".format(out_dir=config["out_dir"], celltype_fragments=config["celltype_fragments"]),
        #             cell_type=wildcards.cell_type),
        # "{celltype_frag_dir}/pseudorep2/{cell_type}_sorted.tsv"
        # "{celltype_frag_dir}/pseudorepT/{cell_type}_sorted.tsv"
    params:
        celltype_frag_dir = "{out_dir}/{celltype_fragments}".format(out_dir=config["out_dir"], celltype_fragments=config["celltype_fragments"]),
        peak_dir = "{out_dir}/{peak_dir}".format(out_dir=config["out_dir"], peak_dir=config["output"]["peaks"]),
        peak_suffix = config["peak_suffix"],
        chrom_size = "{genome_dir}/{genome_build}/{chrom_size}".format(
            genome_dir=config["genome_dir"], genome_build=config["genome_build"], chrom_size=config["genome"][config["genome_build"]]["chrom_sizes"]),
        blacklist = "{genome_dir}/{genome_build}/{blacklist}".format(
            genome_dir=config["genome_dir"], genome_build=config["genome_build"], blacklist=config["genome"][config["genome_build"]]["blacklist"])
    output:
        "{peak_dir}/{cell_type}{peak_suffix}"
    shell:
        """
        echo "scripts/callpeak.sh {cell_type} {params.celltype_frag_dir} {params.peak_dir} {params.chr_size} {params.blacklist}"
        scripts/callpeak.sh {cell_type} {params.celltype_frag_dir} {params.peak_dir} {params.chr_size} {params.blacklist}
        """

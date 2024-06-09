# rules/fragments.smk

SAMPLES = [i.replace(config["frag_suffix"], "") for i in os.listdir(config['input_frag_dir']) if i.endswith(config["frag_suffix"])]

rule zcat:
    input:
        lambda wildcards: expand("{input_frag_dir}/{sample}.tsv.gz", input_frag_dir=config["input_frag_dir"], sample=wildcards.sample),
    params:
        input_frag_dir = config["input_frag_dir"],
        suffix = config["frag_suffix"]
    output:
        "{input_frag_dir}/{sample}.tsv"
    shell:
        """
        echo {input} {output}
        zcat {param.input_frag_dir}/{input} | grep -v '^#' | sed 's/-1\t/\t/g' > {output}
        """


rule sample_fragments:
    input:
        lambda wildcards: expand("{input_barcode_dir}/{sample}-{cell_type}.txt", 
                    input_barcode_dir=config["input_barcode_dir"],
                      sample=wildcards.sample, cell_type=wildcards.cell_type)
    params:
        input_barcode_dir = config["input_barcode_dir"],
        input_file = "{sample}-{cell_type}.txt",
        input_frag_dir = config["input_frag_dir"],
        sample_frag_dir = "{out_dir}/{sample_fragments}".format(out_dir=config["out_dir"], sample_fragments=config["sample_fragments"]),
    output:
        "{sample_frag_dir}/fragments/{cell_type}-{sample}.tsv", 
        "{sample_frag_dir}/pseudorep1/{cell_type}-{sample}.tsv",
        "{sample_frag_dir}/pseudorep2/{cell_type}-{sample}.tsv",
        "{sample_frag_dir}/pseudorepT/{cell_type}-{sample}.tsv"
    threads: 8
    shell:
        """
        # echo "scripts/process_frags.bin {params.input_file} {params.input_barcode_dir}/ {params.input_frag_dir}/ {params.sample_frag_dir}/"
        scripts/process_frags.bin {params.input_file} {params.input_barcode_dir}/ {params.input_frag_dir}/ {params.sample_frag_dir}/
        """

rule sort_cat:
    input:
        lambda wildcards: expand("{sample_frag_dir}/fragments/{cell_type}-{sample}.tsv", 
                    sample_frag_dir="{out_dir}/{sample_fragments}".format(out_dir=config["out_dir"], sample_fragments=config["sample_fragments"]),
                    sample=SAMPLES, cell_type=wildcards.cell_type)
    output:
        "{celltype_frag_dir}/fragments/{cell_type}_sorted.tsv"
        "{celltype_frag_dir}/pseudorep1/{cell_type}_sorted.tsv"
        "{celltype_frag_dir}/pseudorep2/{cell_type}_sorted.tsv"
        "{celltype_frag_dir}/pseudorepT/{cell_type}_sorted.tsv"
    threads: 8
    params:
        celltype_frag_dir = "{out_dir}/{celltype_fragments}".format(out_dir=config["out_dir"], celltype_fragments=config["celltype_fragments"]),
        sample_frag_dir = "{out_dir}/{sample_fragments}".format(out_dir=config["out_dir"], sample_fragments=config["sample_fragments"])

    shell:
        """
        scripts/sort_cat.sh {wildcards.cell_type} {params.sample_frag_dir} {params.celltype_frag_dir}
        """
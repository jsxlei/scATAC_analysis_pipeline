sample_fragment_dir = os.path.join(config["out_dir"], config["sample_fragments"])
print(sample_fragment_dir)
rule zcat:
    input:
        "{frag_dir}/{sample}.tsv.gz"
    output:
        "{frag_dir}/{sample}.tsv"
    params:
        frag_dir = sample_fragment_dir,
        suffix = config["frag_suffix"]
    shell:
        """
        zcat {input} | grep -v '^#' | sed 's/-1\t/\t/g' > {output}
        """
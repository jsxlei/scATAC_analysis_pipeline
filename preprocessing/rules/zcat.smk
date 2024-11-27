rule zcat:
    input:
        config["frag_dir"] + "/{sample}" + config['frag_suffix'] + '.gz'
    params:
        frag_dir = config["frag_dir"]
    output:
        config["frag_dir"] + "/{sample}"+config['frag_suffix']
    shell:
        """
        echo {input} {output}
        zcat {input} | grep -v '^#' | sed 's/-1\t/\t/g' > {output}
        """
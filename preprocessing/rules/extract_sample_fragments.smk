rule extract_sample_fragments:
    input:
        list_input_barcode_files,
        list_input_fragment_files
    params:
        barcode_dir = config["barcode_dir"],
        input_file = "{sample}-{cell_type}.txt",
        frag_dir = config["frag_dir"],
        script = workflow.basedir + "/scripts/process_frags.bin",
    output:
        sample_frag_dir + "/{subfolder}/{cell_type}-{sample}.tsv", 
    threads: 8
    shell:
        """
        echo {output}
        {params.script} {params.input_file} {params.barcode_dir}/ {params.frag_dir}/ {sample_frag_dir}/
        """

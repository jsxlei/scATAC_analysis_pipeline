rule group_celltype:
    input:
        list_sample_fragment_files
    params:
        script = workflow.basedir + "/scripts/sort_cat.sh"
    output:
        celltype_frag_dir + "/{subfolder}/{cell_type}_sorted.tsv"
    threads: 8
    shell:
        """
        bash {params.script} {wildcards.cell_type} {sample_frag_dir} {celltype_frag_dir}
        """

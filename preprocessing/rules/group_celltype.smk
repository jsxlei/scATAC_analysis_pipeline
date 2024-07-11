rule group_celltype:
    input:
        list_sample_fragment_files
    output:
        celltype_frag_dir + "/{subfolder}/{cell_type}_sorted.tsv"
    threads: 8
    shell:
        """
        bash scripts/sort_cat.sh {wildcards.cell_type} {sample_frag_dir} {celltype_frag_dir}
        """
rule report_modisco:
    input:
        output_config["modisco_dir"] + "/{cell_type}/{head}_modisco.h5",
    output:
        report_html = output_config["modisco_dir"] + "/{cell_type}/modisco/{head}/motifs.html",
    params:
        max_seqlets=config['modisco']['max_seqlets'],
        num_leiden=config['modisco']['num_leiden'],
        num_matches=config['modisco']['num_matches'],
        meme_db=motif_config['meme_db'],
        report_outdir=output_config["modisco_dir"] + "/{cell_type}/modisco/{head}",
        img_suffix_dir="./",
    threads: 1
    resources:
        mem_gb=20
    conda:
        "chrombpnet"
    shell:
        """
        modisco report -i {input} -o {params.report_outdir} -s {params.img_suffix_dir} -m {params.meme_db} -n {params.num_matches}
        """
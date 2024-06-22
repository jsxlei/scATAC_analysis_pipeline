rule modisco:
    input:
        output_config["shap_dir"] + "/{cell_type}/average.{head}.h5",
    output:
        modisco_output = output_config["modisco_dir"] + "/{cell_type}/{head}_modisco.h5",
        report_html = output_config["modisco_dir"] + "/{cell_type}/modisco/{head}/motifs.html",
        output_memedb = output_config["modisco_dir"] + "/{cell_type}/{head}_motifs.meme",
    params:
        max_seqlets=config['modisco']['max_seqlets'],
        num_leiden=config['modisco']['num_leiden'],
        num_matches=config['modisco']['num_matches'],
        meme_db=motif_config['meme_db'],
        report_outdir=output_config["modisco_dir"] + "/{cell_type}/motiisco/{head}",
        img_suffix_dir="./",
    threads: 4
    conda:
        "chrombpnet"
    shell:
        """
        modisco motifs -i {input} -n {params.max_seqlets} -l {params.num_leiden} -o {output.modisco_output}
        modisco report -i {output.modisco_output} -o {params.report_outdir} -s {params.img_suffix_dir} -m {params.meme_db} -n {params.num_matches}
        modisco meme -i {output.modisco_output} -t PFM -o {output.output_memedb}
        """
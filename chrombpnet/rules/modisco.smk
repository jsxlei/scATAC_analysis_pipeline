rule modisco:
    input:
        output_config["shap_dir"] + "/{cell_type}/average.{head}.h5",
    output:
        modisco_output = output_config["modisco_dir"] + "/{cell_type}/{head}_modisco.h5",
        # report_html = output_config["modisco_dir"] + "/{cell_type}/modisco/{head}/motifs.html",
    params:
        max_seqlets=config['modisco']['max_seqlets'],
        num_leiden=config['modisco']['num_leiden'],
        num_matches=config['modisco']['num_matches'],
        meme_db=motif_config['meme_db'],
        report_outdir=output_config["modisco_dir"] + "/{cell_type}/modisco/{head}",
        img_suffix_dir="./",
    threads: 8
    resources:
        mem_gb=80
    conda:
        "chrombpnet"
    shell:
        """
        if [[ -f {output.modisco_output} ]]; then
            echo "Found modisco_h5"
        else
            modisco motifs -i {input} -n {params.max_seqlets} -l {params.num_leiden} -o {output.modisco_output}
        fi

        """
        
rule report_pipeline:
    input:
        average_shap=list_average_shap,
        modisco=list_modisco,
        hitcaller=list_hitcaller,
        predictions=list_predictions,
        models=list_models,
        negatives=list_negatives,
    output:
        summary_md=output_config["report_dir"] + "/summary.md",
        summary_json=output_config["report_dir"] + "/summary.json",
        file_stats_tsv=output_config["report_dir"] + "/file_stats.tsv",
        peak_stats_tsv=output_config["report_dir"] + "/peak_stats.tsv",
        runtime_stats_tsv=output_config["report_dir"] + "/runtime_stats.tsv",
        status_json=output_config["status_dir"] + "/status.json",
        status_md=output_config["status_dir"] + "/status.md",
    params:
        out_dir=config["out_dir"],
        report_dir=output_config["report_dir"],
        status_dir=output_config["status_dir"],
        peak_dir=config["peak_dir"],
        peak_suffix=config["peak_suffix"],
        union_peak=config["union_peak"],
        use_union_peaks=USE_UNION_PEAKS,
        celltypes=",".join(CELLTYPES),
        snakemake_dir=workflow.basedir + "/.snakemake",
    conda:
        "chrombpnet"
    script:
        "../scripts/pipeline_report_rule.py"

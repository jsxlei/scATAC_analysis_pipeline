rule make_datahub:
    input:
    output:
    params:
        script = workflow.basedir + '/scripts/genome_browser.py',
        path = config['out_dir'],
        heads = ' '.join(config['head']),
        peak_suffix = config['peak_suffix']
    shell:
        """
        python {params.script} \
            --path {params.path} \
            --heads {params.heads} \
            --peak_suffix {params.peak_suffix}
        """

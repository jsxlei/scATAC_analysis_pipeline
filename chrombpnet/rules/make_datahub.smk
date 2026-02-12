rule make_datahub:
    input:
    output:
    params:
        script = workflow.basedir + '/scripts/genome_browser.py',
    shell:
        """
        python {params.script} 
        """
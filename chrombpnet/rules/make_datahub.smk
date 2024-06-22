rule make_datahub:
    input:
    output:
    params:
    shell:
        """
        make_igv_session \
            -i H5PY \
            -o OUTPUT_PREFIX \
            #[-l N_LEIDEN] [-w WINDOW] [-v]

        """
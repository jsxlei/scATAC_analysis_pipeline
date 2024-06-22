rule footprints:
    input:
    output:
    params:
    shell:
        """
        footprints \
            -i H5PY \
            -o OUTPUT_PREFIX \
            #[-l N_LEIDEN] [-w WINDOW] [-v]

        """
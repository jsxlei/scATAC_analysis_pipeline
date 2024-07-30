rule hitcaller:
    input:
        shap_h5 = output_config["shap_dir"] + "/{cell_type}/average.{head}.h5",
        modisco_h5 = output_config["modisco_dir"] + "/{cell_type}/{head}_modisco.h5",
        peaks_bed = config["union_peak"],
    output:
        finemo_npz = output_config["hitcaller_dir"] + "/{cell_type}/{head}/regions.npz",
        finemo_hits = output_config["hitcaller_dir"] + "/{cell_type}/{head}/hits.tsv",
        finemo_bed = output_config["hitcaller_dir"] + "/{cell_type}/{head}/hits.bed.gz",
    params:
        finemo_out = output_config["hitcaller_dir"] + "/{cell_type}/{head}",
        alpha = config['alpha'],
    conda:
        "finemo_gpu"
    threads: 16
    shell:
        """
        finemo extract-regions-h5 --h5s {input.shap_h5} --out-path {output.finemo_npz} --region-width 1000
        finemo call-hits --regions {output.finemo_npz} --modisco-h5 {input.modisco_h5} --peaks {input.peaks_bed} --alpha {params.alpha} --out-dir {params.finemo_out}
        finemo report --hits {output.finemo_hits} --regions {output.finemo_npz} --modisco-h5 {input.modisco_h5} --peaks {input.peaks_bed} --out-dir {params.finemo_out}

        if [[ -f "{params.finemo_out}/hits.bed" ]]; then 
            
            # bgzip and index hits
            module load biology samtools

            bgzip -c {params.finemo_out}/hits.bed > {params.finemo_out}/hits.bed.gz
            tabix -p bed {params.finemo_out}/hits.bed.gz

        fi
        """
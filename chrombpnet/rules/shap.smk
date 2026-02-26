import pandas as pd


def _count_peaks(path):
    return pd.read_csv(path, sep="\t").shape[0]


def _shap_mem_gb(wildcards, input, attempt):
    return max(_count_peaks(input.peaks_file) / 5000, 60)

rule shap:
    input:
        model = output_config["model_dir"] + "/{cell_type}/{fold}/models/chrombpnet_nobias.h5",
        peaks_file = config["union_peak"] if USE_UNION_PEAKS else config["peak_dir"] + "/{cell_type}" + config["peak_suffix"],
    output: 
        shap_bw = output_config["shap_dir"] + "/{cell_type}/{fold}.{head}_scores.bw",
        shap_h5 = output_config["shap_dir"] + "/{cell_type}/{fold}.{head}_scores.h5",
    params:
        fasta = genome_config["fasta"],
        chrom_sizes = genome_config["chrom_sizes"],
        output_prefix = output_config["shap_dir"] + "/{cell_type}/{fold}",
        shap_dir = output_config["shap_dir"],
        
    resources:
        nvidia_gpu=1,
        mem_gb=_shap_mem_gb,
    conda:
        "chrombpnet"
    threads: 2
    shell:
        """
        mkdir -p {params.shap_dir}

        if [[ -f {output.shap_bw} ]]; then
            echo "Found {wildcards.head} shap scores"
        else
            echo "Generate {wildcards.head} contribution score bigwigs"
            chrombpnet contribs_bw \
                -m {input.model} \
                -r {input.peaks_file} \
                -g {params.fasta} \
                -c {params.chrom_sizes} \
                -op {params.output_prefix} \
                -pc {wildcards.head}
        fi
        """

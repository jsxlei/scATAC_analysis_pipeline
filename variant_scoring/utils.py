import numpy as np
import pandas as pd
import multiprocessing
# from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from functools import partial, wraps

# pd.options.mode.chained_assignment = None

# global promoter_df, exon_df, gene_df
##############
# ANNOTATION #
##############
def annotate_variants(variants_df):
    # Variant type (SNP/indel)
    print("computing variant type...")
    variants_df["ref_length"] = variants_df["ref"].str.len()
    variants_df["alt_length"] = variants_df["alt"].str.len()
    variants_df["allele_length_delta"] = (
        variants_df["alt_length"] - variants_df["ref_length"]
    )
    variants_df["variant_type"] = ""
    variants_df.loc[
        (variants_df["allele_length_delta"] == 0) & (variants_df["ref_length"] == 1),
        "variant_type",
    ] = "SNV"
    variants_df.loc[
        (variants_df["allele_length_delta"] == 0) & (variants_df["ref_length"] > 1),
        "variant_type",
    ] = "substitution"
    variants_df.loc[variants_df["allele_length_delta"] > 0, "variant_type"] = (
        "insertion"
    )
    variants_df.loc[variants_df["allele_length_delta"] < 0, "variant_type"] = "deletion"
    variants_df["variant_length"] = np.maximum(
        variants_df["ref_length"], variants_df["alt_length"]
    )
    # Variant region (promoter/exonic/intronic/intergenic)
    # Gene
    print("loading genes...")
    gene_df = pd.read_csv(
        "/users/salil512/experiments/GENCODE_transcripts/gene_df.tsv", sep="\t"
    )
    gene_df = gene_df[gene_df["gene_type"] == "protein_coding"]
    gene_set = set(gene_df["gene"])
    # Promoter
    print("loading promoters...")
    promoter_df = pd.read_csv(
        "/users/salil512/experiments/GENCODE_transcripts/transcript_df.tsv", sep="\t"
    )
    promoter_df = promoter_df[promoter_df["gene"].isin(gene_set)]
    # print(promoter_df.head())
    # Exon
    print("loading exons...")
    exon_df = pd.read_csv(
        "/users/salil512/experiments/GENCODE_transcripts/exon_df.tsv", sep="\t"
    )
    exon_df = exon_df[exon_df["gene"].isin(gene_set)]
    # Assign regions
    print("computing regions...")
    num_processes = 32
    variants_split = np.array_split(variants_df, num_processes)
    payloads = [(x, promoter_df, exon_df, gene_df) for x in variants_split]
    with multiprocessing.Pool(processes=32) as p:
        region_subsets = p.starmap(_region_annotations, payloads)
    regions = []
    for rs in region_subsets:
        regions += rs
    variants_df["region_type"] = regions

    # 3 Nearest genes
    print("computing 3 nearest genes...")
    nearest_gene_1, nearest_gene_2, nearest_gene_3 = _find_3_nearest_genes(
        variants_df, gene_df
    )
    variants_df["nearest_gene"] = nearest_gene_1
    variants_df["2nd_nearest_gene"] = nearest_gene_2
    variants_df["3rd_nearest_gene"] = nearest_gene_3
    gene_within_100kb = (
        np.abs(
            variants_df["nearest_gene"]
            .str.split("(")
            .str[1]
            .str.split(")")
            .str[0]
            .astype(int)
        )
        <= 100000
    )
    variants_df["gene_within_100kb"] = gene_within_100kb
    # Return
    return variants_df

# partial(function, promoter_df=promoter_df, exon_df=exon_df, gene_df=gene_df)

# Define the decorator for paralellizing the extraction of loci
def parallelize(pool_size=None, desc='', disable=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not pool_size:
                num_cores = cpu_count()
                num_workers = max(1, num_cores // 2)
            else:
                num_workers = pool_size

            print(f"Using {num_workers} workers for parallel processing.")
            with Pool(processes=num_workers) as pool:
                # Ensure that the DataFrame or other iterable is the first argument
                data_iterable = args[0]
                func_partial = partial(func, *args[1:], **kwargs)
                data = list(tqdm(pool.imap(func_partial, data_iterable.itertuples(index=False, name=None)), desc=desc, disable=disable, total=len(data_iterable)))

            return data
        return wrapper
    return decorator


def _region_annotations(row, promoter_df, exon_df, gene_df):
    # for _, row in tqdm(variants_df.iterrows(), total=len(variants_df)):
    # c, p = row["chr"], row["pos"]
    # print(row)
    c, p = row[:2]
    if (
        len(
            promoter_df[
                (promoter_df["chro"] == c)
                & ((promoter_df["promoter_start"] - p) * (promoter_df["promoter_end"] - p) <= 0)
            ]
        )
        > 0
    ):
        return "promoter"
    elif (
        len(
            exon_df[
                (exon_df["chro"] == c)
                & ((exon_df["start"] - p) * (exon_df["end"] - p) <= 0)
            ]
        )
        > 0
    ):
        return "exonic"
        # regions.append("exonic")
    elif (
        len(
            gene_df[
                (gene_df["chro"] == c)
                & ((gene_df["start"] - p) * (gene_df["end"] - p) <= 0)
            ]
        )
        > 0
    ):
        # regions.append("intronic")
        return "intronic"
    else:
        # regions.append("intergenic")
        return "intergenic"
    # return regions


def _find_3_nearest_genes(variants_df, gene_df):
    genes_by_chro = {
        chro: gene_df[gene_df["chro"] == chro].copy() for chro in set(gene_df["chro"])
    }
    genes0 = []
    genes1 = []
    genes2 = []
    for index, row in variants_df.iterrows():
        chro, pos = row["chr"], row["pos"]
        genes_chro = genes_by_chro[chro]
        genes_chro["strand_sign"] = 1 * (genes_chro["strand"] == "+") - 1 * (
            genes_chro["strand"] == "-"
        )
        genes_chro["start_dist"] = (pos - genes_chro["start"]) * genes_chro[
            "strand_sign"
        ]
        genes_chro["end_dist"] = (pos - genes_chro["end"]) * genes_chro["strand_sign"]
        genes_chro["var_in_gene"] = 1 * (
            genes_chro["start_dist"] * genes_chro["end_dist"] <= 0
        )
        genes_chro["dist"] = np.minimum(
            np.abs(genes_chro["start_dist"]), np.abs(genes_chro["end_dist"])
        ) * (1 - genes_chro["var_in_gene"])
        genes_chro["signed_dist"] = genes_chro["dist"] * (
            genes_chro["strand_sign"] * np.sign(genes_chro["start_dist"])
        )
        genes_chro = genes_chro.sort_values(by=["dist"], ascending=True)
        genes_chro = genes_chro.reset_index(drop=True)
        genes0.append(
            f"{genes_chro.loc[0, 'gene']} ({genes_chro.loc[0, 'signed_dist']})"
        )
        genes1.append(
            f"{genes_chro.loc[1, 'gene']} ({genes_chro.loc[1, 'signed_dist']})"
        )
        genes2.append(
            f"{genes_chro.loc[2, 'gene']} ({genes_chro.loc[2, 'signed_dist']})"
        )
    return genes0, genes1, genes2


##################
# PRIORITIZATION #
##################
def prioritize_variants(variants_df, scores_loc, peaks_loc):
    scores_df = _load_score_files(scores_loc)
    scores_df["ref"] = scores_df["allele1"]
    scores_df["alt"] = scores_df["allele2"]
    # scores_df['variant_id'] = scores_df['chr'].astype(str) + ':' + scores_df['pos'].astype(str) + ':' + scores_df['ref'] + ':' + scores_df['alt']
    scores_df["region_type"] = variants_df["region_type"]
    scores_df["nearest_gene"] = variants_df["nearest_gene"]
    scores_df["2nd_nearest_gene"] = variants_df["2nd_nearest_gene"]
    scores_df["3rd_nearest_gene"] = variants_df["3rd_nearest_gene"]
    peaks_chrodict = _load_peaks_chrodict(peaks_loc)
    scores_df["in_peak"] = _assign_peaks(scores_df, peaks_chrodict)
    prioritized = []
    for index, row in scores_df.iterrows():
        p = (
            (row["gavg_abs_logfc_pval"] <= 0.01)
            & (row["avg_active_allele_quantile"] >= 0.05)
            & (
                (row["region_type"] == "promoter")
                | (row["in_peak"] == "in_peak")
                | ((row["in_peak"] == "out_of_peak") & (row["avg_logfc"] > 0))
            )
        )
        prioritized.append(p)
    scores_df["prioritized"] = prioritized
    return scores_df


def _load_score_files(score_file_base):
    # LOAD FILES
    score_files = [f"{score_file_base}/fold_{f}/.variant_scores.tsv" for f in range(5)]
    score_dfs = [pd.read_csv(sf, sep="\t", header=0) for sf in score_files]
    # SUBSET IMPORTANT COLUMNS
    for i, sdf in enumerate(score_dfs):
        score_dfs[i] = sdf[
            [
                "chr",
                "pos",
                "allele1",
                "allele2",
                "variant_id",
                "allele1_pred_counts",
                "allele1_quantile", 
                "allele2_pred_counts",
                "allele2_quantile", 
                "active_allele_quantile", 
                "logfc",
                "abs_logfc",
                "abs_logfc.pval",
            ]
        ]
    # COLLATE COMMON VARIANT INFO
    average_df = pd.DataFrame()
    for z in ["chr", "pos", "allele1", "allele2", "variant_id"]:
        average_df[z] = score_dfs[0][z]
    # COLLATE FOLD-SPECIFIC INFO
    scores_to_collate = [
        "allele1_pred_counts",
        "allele1_quantile", #"allele1_percentile",
        "allele2_pred_counts",
        "allele2_quantile", #"allele2_percentile",
        "active_allele_quantile", #"active_allele_quantile",
        "logfc",
        "abs_logfc",
        "abs_logfc.pval",
    ]
    for score in scores_to_collate:
        for i in range(5):
            average_df[f"{score}_{i}"] = score_dfs[i][f"{score}"]
    # COLLATE ACROSS-FOLD AVERAGES
    average_df["avg_logfc"] = (
        average_df["logfc_0"]
        + average_df["logfc_1"]
        + average_df["logfc_2"]
        + average_df["logfc_3"]
        + average_df["logfc_4"]
    ) / 5
    average_df["avg_abs_logfc"] = (
        average_df["abs_logfc_0"]
        + average_df["abs_logfc_1"]
        + average_df["abs_logfc_2"]
        + average_df["abs_logfc_3"]
        + average_df["abs_logfc_4"]
    ) / 5
    average_df["gavg_abs_logfc_pval"] = (
        average_df["abs_logfc.pval_0"]
        * average_df["abs_logfc.pval_1"]
        * average_df["abs_logfc.pval_2"]
        * average_df["abs_logfc.pval_3"]
        * average_df["abs_logfc.pval_4"]
    ) ** (1 / 5)
    average_df["avg_active_allele_quantile"] = (
        average_df["active_allele_quantile_0"]
        + average_df["active_allele_quantile_1"]
        + average_df["active_allele_quantile_2"]
        + average_df["active_allele_quantile_3"]
        + average_df["active_allele_quantile_4"]
    ) / 5
    # INDEX
    average_df["index"] = average_df.index
    return average_df


def _assign_peaks(variants_df, peak_chrodict):
    in_peaks = []
    for _, row in variants_df.iterrows():
        c, p = row["chr"], row["pos"]
        peaks_c = peak_chrodict[c]
        num_overlap_peaks = len(
            peaks_c[(peaks_c["start"] - p) * (peaks_c["stop"] - p) <= 0]
        )
        in_peaks.append("in_peak" if num_overlap_peaks > 0 else "out_of_peak")
    return in_peaks

def _load_peaks_chrodict(peaks_loc):
    if peaks_loc.endswith(".gz"):
        peak_df = pd.read_csv(
            peaks_loc,
            sep="\t",
            names=["chro", "start", "stop", "4", "5", "6", "7", "8", "9", "summit"],
            compression="gzip",
        )
    else:
        peak_df = pd.read_csv(
            peaks_loc,
            sep="\t",
            names=["chro", "start", "stop", "4", "5", "6", "7", "8", "9", "summit"],
        )
    return {c: peak_df[peak_df["chro"] == c] for c in set(peak_df["chro"])}
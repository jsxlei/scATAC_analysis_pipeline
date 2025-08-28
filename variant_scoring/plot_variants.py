import os.path
import ast
import sys
import time
import hashlib
from collections import defaultdict
import numpy as np
import pandas as pd
import deepdish
import h5py
import multiprocessing
import polars as pl


import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import logomaker
def load_peaks_4(peaks_loc):
    peak_df = pd.read_csv(peaks_loc, sep="\t", names=["chro", "start", "stop", "name"])
    peak_finder = dict()
    for chro in set(peak_df["chro"]):
        peak_finder[chro] = peak_df[peak_df["chro"] == chro]
    return peak_finder


def load_peaks_10(peaks_loc):
    peak_df = pd.read_csv(peaks_loc, sep="\t", names=["chro", "start", "stop", "4", "5", "6", "7", "8", "9", "summit"])
    peak_df["name"] = peak_df["chro"] + ":" + peak_df["start"].astype(str) + ":" + peak_df["stop"].astype(str)
    peak_finder = dict()
    for chro in set(peak_df["chro"]):
        peak_finder[chro] = peak_df[peak_df["chro"] == chro]
    return peak_finder


def assign_peaks(variants_df, peaks_loc, peaks_name, num_cols):
    if num_cols == 4:
        peak_finder = load_peaks_4(peaks_loc)
    elif num_cols == 10:
        peak_finder = load_peaks_10(peaks_loc)
    else:
        assert(False)
    in_peaks = []
    for index, row in variants_df.iterrows():
        chro, pos, ref = row["chr"], row["pos"], row["ref"]
        pos_start = pos
        pos_end = pos + len(ref) - 1
        if chro not in peak_finder:
            in_peaks.append("out_of_peak")
            continue
        else:
            peak_chro = peak_finder[chro]
        # Option 1 - variant start is within region
        match_1 = peak_chro[(peak_chro["start"] <= pos_start) & (peak_chro["stop"] >= pos_start)]
        # Option 2 - variant stop is within region
        match_2 = peak_chro[(peak_chro["start"] <= pos_end) & (peak_chro["stop"] >= pos_end)]
        # Option 3 - variant region encapsulates a whole region
        match_3 = peak_chro[(peak_chro["start"] >= pos_start) & (peak_chro["stop"] <= pos_end)]
        # Combine all matches
        all_matches_df = pd.concat([match_1, match_2, match_3], axis=0, ignore_index=True)
        all_matches_df.drop_duplicates(inplace=True)
        # In peak or not
        in_peaks.append(" & ".join(list(all_matches_df["name"])) if len(all_matches_df) > 0 else "out_of_peak")
    return {peaks_name: in_peaks}


def assign_peaks_parallel(variants_df, peaks_dict, num_cols=10):
    inputs = []
    for peaks_name, peaks_loc in peaks_dict.items():
        inputs.append((variants_df, peaks_loc, peaks_name, num_cols))
    with multiprocessing.Pool() as pool:
        results = pool.starmap(assign_peaks, inputs)
        pool.close()
        pool.join()
    for x in results:
        for pn, ip in x.items():		
            variants_df[pn] = ip
    return variants_df

def _plotter_profile(allele1_profiles, allele2_profiles, vlines, ax0, allele1_label, allele2_label):
    xmins, xmaxs = [], []
    shortened_allele1_label = allele1_label if len(allele1_label) < 15 else f"{allele1_label[:15]}... (len {len(allele1_label)})"
    for i, (x, allele1_profile) in enumerate(allele1_profiles):
        ax0.plot(x, allele1_profile, label=(f"ref ({shortened_allele1_label})" if i==0 else ""), color='C0')
        xmins.append(min(x)); xmaxs.append(max(x))
    shortened_allele2_label = allele2_label if len(allele2_label) < 15 else f"{allele2_label[:15]}... (len {len(allele2_label)})"
    for i, (x, allele2_profile) in enumerate(allele2_profiles):
        ax0.plot(x, allele2_profile, label=(f"alt ({shortened_allele2_label})" if i==0 else ""), color='C1')
        xmins.append(min(x)); xmaxs.append(max(x))
    for v in vlines:
        ax0.axvline(v, color='black', ls='--', linewidth=1)
    xmin, xmax = min(xmins), max(xmaxs)
    ax0.set_xlim(xmin, xmax)
    ax0.set_xticks(np.arange(xmin + (50 - xmin%50)%50, xmax+1, 50))
    ax0.legend(prop={'size': 12}, loc='upper right')


def _plotter_shap(allele1_shap, allele2_shap, vlines, xmin, ax1, ax2, allele1_label, allele2_label):
    active_allele = "ref" if np.sum(allele1_shap) > np.sum(allele2_shap) else "alt"
    df1 = pd.DataFrame(allele1_shap, columns=["A", "C", "G", "T"])
    df1.index +=  xmin
    df2 = pd.DataFrame(allele2_shap, columns=["A", "C", "G", "T"])
    df2.index += xmin
    logomaker.Logo(df1, ax=ax1)
    logomaker.Logo(df2, ax=ax2)
    for v in vlines:
        ax1.axvline(v, color='k', linestyle='--', linewidth=1)
        ax2.axvline(v, color='k', linestyle='--', linewidth=1)
    ymax = 1.1*max(np.max(np.maximum(allele1_shap, 0)), np.max(np.maximum(allele2_shap, 0)))
    ymin = 1.1*min(np.min(np.minimum(allele1_shap, 0)), np.min(np.minimum(allele2_shap, 0)))
    ax1.set_ylim(bottom=ymin, top=ymax)
    ax2.set_ylim(bottom=ymin, top=ymax)
    shortened_allele_1_label = allele1_label if len(allele1_label) < 15 else f"{allele1_label[:15]}... (len {len(allele1_label)})"
    plt.text(0.988, 0.903, f"ref ({shortened_allele_1_label})", 
                             verticalalignment='top', horizontalalignment='right',
                             transform=ax1.transAxes, size=12, color='black',
                             bbox=dict(boxstyle='round', facecolor='white', edgecolor='lightgrey'))
    shortened_allele2_label = allele2_label if len(allele2_label) < 15 else f"{allele2_label[:15]}... (len {len(allele2_label)})"
    plt.text(0.988, 0.903, f"alt ({shortened_allele2_label})", 
                             verticalalignment='top', horizontalalignment='right',
                             transform=ax2.transAxes, size=12, color='black',
                             bbox=dict(boxstyle='round', facecolor='white', edgecolor='lightgrey'))


def _plot_profile(allele1_pred, allele2_pred, allele1_length, allele2_length, allele1_label, allele2_label, window_size, ax0):
    total_length = 1000
    C = total_length//2
    F = window_size//2
    if allele1_length < allele2_length:
        # INSERTION
        allele1_pred_plots = []
        allele1_pred_plots.append((list(range(-F, allele1_length)), allele1_pred[C-F:C+allele1_length]))
        allele1_pred_plots.append((list(range(allele2_length, F+allele2_length)),
                                  allele1_pred[C+allele1_length:C+F+allele1_length]))
        allele2_pred_plots = [(list(range(-F, F+allele2_length)), allele2_pred[C-F:C+F+allele2_length])]
        vlines = [-0.5, allele2_length-0.5]
    elif allele1_length > allele2_length:
        # DELETION
        allele1_pred_plots = [(list(range(-F, F+allele1_length)), allele1_pred[C-F:C+F+allele1_length])]
        allele2_pred_plots = []
        allele2_pred_plots.append((list(range(-F, allele2_length)), allele2_pred[C-F:C+allele2_length]))
        allele2_pred_plots.append((list(range(allele1_length, F+allele1_length)),
                                  allele2_pred[C+allele2_length:C+F+allele2_length]))
        vlines = [-0.5, allele1_length-0.5]
    else:
        # SUBSTITUTION
        allele1_pred_plots = [(list(range(-F, F+allele1_length)), allele1_pred[C-F:C+F+allele1_length])]
        allele2_pred_plots = [(list(range(-F, F+allele2_length)), allele2_pred[C-F:C+F+allele2_length])]
        vlines = [-0.5, +allele1_length-0.5]
    _plotter_profile(allele1_pred_plots, allele2_pred_plots, vlines, ax0, allele1_label, allele2_label)


def _plot_shap(allele1_shap, allele2_shap, allele1_length, allele2_length, allele1_label, allele2_label, window_size, ax1, ax2):
    total_length = 2114
    C = total_length//2
    F = window_size//2
    if allele1_length < allele2_length:
        # INSERTION
        allele1_shap_plot = np.concatenate([allele1_shap[C-F:C+allele1_length],
                                           np.zeros((allele2_length-allele1_length, 4)),
                                           allele1_shap[C+allele1_length:C+F+allele1_length]])
        allele2_shap_plot = allele2_shap[C-F:C+F+allele2_length]
        vlines = [-0.5, allele2_length-0.5]
    elif allele1_length > allele2_length:
        # DELETION
        allele1_shap_plot = allele1_shap[C-F:C+F+allele1_length]
        allele2_shap_plot = np.concatenate([allele2_shap[C-F:C+allele2_length],
                                           np.zeros((allele1_length-allele2_length, 4)),
                                           allele2_shap[C+allele2_length:C+F+allele2_length]])
        vlines = [-0.5, allele1_length-0.5]
    else:
        # SUBSTITUTION
        allele1_shap_plot = allele1_shap[C-F:C+F+allele1_length]
        allele2_shap_plot = allele2_shap[C-F:C+F+allele2_length]
        vlines = [-0.5, allele1_length-0.5]
    assert(allele1_shap_plot.shape == allele2_shap_plot.shape)
    _plotter_shap(allele1_shap_plot, allele2_shap_plot, vlines, -F, ax1, ax2, allele1_label, allele2_label)


def plot_variant(allele1_pred, allele2_pred, allele1_shap, allele2_shap, allele1_length, allele2_length, allele1_label, allele2_label, window_size, title, save_loc):
    fig, axs = plt.subplots(3, 1, figsize=(20, 8), dpi=400)
    # PLOT PROFILE
    _plot_profile(allele1_pred, allele2_pred, allele1_length, allele2_length, allele1_label, allele2_label, window_size, axs[0])
    # PLOT SHAP
    _plot_shap(allele1_shap, allele2_shap, allele1_length, allele2_length, allele1_label, allele2_label, window_size, axs[1], axs[2])
    # PLOT
    plt.suptitle(title, fontsize=24, y=0.93)
    plt.subplots_adjust(hspace=0.3, top=0.785)
    fig.set_facecolor('white')
    plt.savefig(save_loc, bbox_inches='tight')
    # plt.savefig(save_loc, bbox_inches='tight', format='svg', dpi=300)
    plt.close()


def load_scores(file_prefix):
    counts1, counts2, profile1, profile2 = {}, {}, {}, {}
    chrs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 'X', 'Y']

    def softmax(x, temp=1):
        norm_x = x - np.mean(x, axis=1, keepdims=True)
        return np.exp(temp*norm_x)/np.sum(np.exp(temp*norm_x), axis=1, keepdims=True)

    fold_preds1 = []
    fold_preds2 = []
    existing_folds = []
    for f in range(5):
        # List of HDF5 files to merge
        # fold_h5_files = [f"{file_prefix}/fold_{f}/.variant_predictions.h5" for chr in chrs]
        # fold_h5_files = [f"{file_prefix}/fold_{f}/.chr{chr}.variant_predictions.h5" for chr in chrs]
        file = f"{file_prefix}/fold_{f}/preds/.variant_predictions.h5"

        # fold_counts1 = []
        # fold_counts2 = []
        # fold_profile1 = []
        # fold_profile2 = []
        # fold_preds1 = []
        # fold_preds2 = []

        # for file in fold_h5_files:
            # Check if file exists
        if not os.path.exists(file):
            print(file)
            continue
        existing_folds.append(f)
        # print(f"Loading {file}")
        with h5py.File(file, 'r') as h5file:
            # fold_counts1.append(h5file["observed"]["allele1_pred_counts"][:])
            # fold_counts2.append(h5file["observed"]["allele2_pred_counts"][:])
            # fold_profile1.append(h5file["observed"]["allele1_pred_profiles"][:])
            # fold_profile2.append(h5file["observed"]["allele2_pred_profiles"][:])
            fold_preds1.append(h5file["observed"]["allele1_pred_counts"][:] * softmax(h5file["observed"]["allele1_pred_profiles"][:]))
            fold_preds2.append(h5file["observed"]["allele2_pred_counts"][:] * softmax(h5file["observed"]["allele2_pred_profiles"][:]))
        
        # counts1[f] = np.concatenate(fold_counts1, axis=0)
        # counts2[f] = np.concatenate(fold_counts2, axis=0)
        # profile1[f] = np.concatenate(softmax(fold_profile1), axis=0)
        # profile2[f] = np.concatenate(softmax(fold_profile2), axis=0)

    # Handling zeros and negatives before taking the log
    # for i in range(5):
    # 	counts1[i][counts1[i] <= 0] = np.nan
    # 	counts2[i][counts2[i] <= 0] = np.nan
    # 	profile1[i][profile1[i] <= 0] = np.nan
    # 	profile2[i][profile2[i] <= 0] = np.nan

    # counts1["avg_counts"] = np.mean(np.array([counts1[fold] for fold in range(5)]), axis=0)
    # counts2["avg_counts"] = np.mean(np.array([counts2[fold] for fold in range(5)]), axis=0)
    # profile1["avg_profile"] = np.mean(np.array([profile1[fold] for fold in range(5)]), axis=0)
    # profile2["avg_profile"] = np.mean(np.array([profile2[fold] for fold in range(5)]), axis=0)

    # counts_profile_1 = counts1["avg_counts"] * profile1["avg_profile"]
    # counts_profile_2 = counts2["avg_counts"] * profile2["avg_profile"]
    avg_preds1 = np.mean(np.array([fold_preds1[fold] for fold in range(len(fold_preds1))]), axis=0)
    avg_preds2 = np.mean(np.array([fold_preds2[fold] for fold in range(len(fold_preds2))]), axis=0)
    # avg_preds1 = np.mean(np.array([fold_preds1[fold] for fold in existing_folds]), axis=0)
    # avg_preds2 = np.mean(np.array([fold_preds2[fold] for fold in existing_folds]), axis=0)
    # assert counts_profile_1.shape == counts_profile_2.shape
    # return counts_profile_1, counts_profile_2
    return avg_preds1, avg_preds2


def load_shaps(file_prefix, type='counts'):
    shaps1 = None
    shaps2 = None
    existing_folds = []
    for f in range(5):
        file = f"{file_prefix}/fold_{f}/shap/.variant_shap.{type}.h5"
        if not os.path.exists(file):
            print(file)
            continue
        existing_folds.append(f)
        fold_shaps = deepdish.io.load(file)
        shaps_f = fold_shaps["projected_shap"]["seq"]
        N = shaps_f.shape[0]//2
        if shaps1 is None:
            shaps1 = shaps_f[:N, :, :]
            shaps2 = shaps_f[N:, :, :]
        else:
            shaps1 += shaps_f[:N, :, :]
            shaps2 += shaps_f[N:, :, :]
    shaps1 = np.transpose(shaps1/5, (0, 2, 1))
    shaps2 = np.transpose(shaps2/5, (0, 2, 1))
    assert(shaps1.shape == shaps2.shape)
    return shaps1, shaps2


def load_list(list_loc):
    with open(list_loc, 'r') as f:
        return [line.strip() for line in f]

def parse_models_completed(cell):
    try:
        return ast.literal_eval(cell)
    except (ValueError, SyntaxError):
        return [cell] if cell != '[]' else []



from multiprocessing import Pool

def parallel_func(df, func, n_cores=20):
    df_split = np.array_split(df, n_cores)
    pool = Pool(n_cores)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    
    return df


def plot_variants(df, models, pred_path_, shap_path_, out_dir):
    for i, row in df.iterrows(): #named=True)):
        # print(i, row) 
        variant_name = row['rsid'] #row["variant_name"]
        # models = os.listdir(shap_path_)
        for model in models:
            os.makedirs(os.path.join(out_dir, model), exist_ok=True)
            pred_path = os.path.join(pred_path_, model)
            shap_path = os.path.join(shap_path_, model) 
            if not os.path.exists(pred_path):
                continue
            # print(pred_path, shap_path)
            counts_profile_1, counts_profile_2 = load_scores(pred_path)
            shaps1, shaps2 = load_shaps(shap_path, type='counts')
            ref_profile = counts_profile_1[i, :]
            alt_profile = counts_profile_2[i, :]
            ref_shap = shaps1[i, :, :]
            alt_shap = shaps2[i, :, :]
            ref_length = len(row["allele1"])
            alt_length = len(row["allele2"])
            ref_label = row["allele1"]
            alt_label = row["allele2"]
            title = f'{variant_name} Profile Predictions & Contribution Scores in ({model}) Model'
            # file_out = f'/oak/stanford/groups/akundaje/airanman/nautilus-sync/gloyn-heart-010825/figures/profiles/{variant_name}.{model}.jpg'
            file_out = os.path.join(out_dir, model, f'{variant_name}.jpg')
            plot_variant(ref_profile, alt_profile, ref_shap, alt_shap, ref_length, alt_length, ref_label, alt_label, 300, title, file_out)
            print(f'Wrote to {file_out}')
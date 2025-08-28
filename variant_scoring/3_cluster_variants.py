import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import os
from sklearn.cluster import KMeans

import argparse
from matplotlib.patches import Patch

parser = argparse.ArgumentParser()
parser.add_argument("--work_dir", '-p', type=str)
# parser.add_argument("--prioritized_variants_loc", '-p', type=str)
# parser.add_argument("--clustered_variants_loc", '-c', type=str)
parser.add_argument("--n_clusters", type=int, default=10)
parser.add_argument("--seed", type=int, default=1234)
# parser.add_argument("--cluster_plot_loc", type=str, default=None)
args = parser.parse_args()

# np.random.seed(args.seed)
## e.g. python ~/pipeline/variant_scoring/3_cluster_variants.py --work_dir /users/leixiong/project/variants/annotation/human_tomq

###
# PARAMETERS
###
prioritized_variants_loc = os.path.join(args.work_dir, "prioritized_variants.tsv")
clustered_variants_loc = os.path.join(args.work_dir, "clustered_variants.tsv")
n_clusters = args.n_clusters
cluster_plot_loc = os.path.join(args.work_dir, "variant_clusters.pdf")

###
# CODE
###
print("loading variants...")
variants = pd.read_csv(prioritized_variants_loc, sep="\t")
variants_prioritized = variants[variants["prioritized"]]
prioritized_scores = np.abs(
    variants_prioritized[
        [x for x in variants_prioritized.columns if x.startswith("score-")]
    ]
)
# prioritized_scores = variants_prioritized.filter(like='LFC-', axis=1)

print("cluster...")
column_order = list(variants.columns) + ['kmeans_clusters']
print('kmeans_clusters' in column_order)
# _column_order = column_order.copy()


kmeans_clusters = KMeans(
    n_clusters=n_clusters, n_init="auto", max_iter=2000, tol=1e-8, random_state=args.seed, n_init=50
).fit_predict(prioritized_scores)
            
clustered_idx_dict = {x: i for i, x in enumerate(list(prioritized_scores.index))}
variants["kmeans_cluster"] = [
    kmeans_clusters[clustered_idx_dict[i]] if i in clustered_idx_dict else "None"
    for i in range(len(variants))
]

print("reorder columns...")
# column_order.insert(column_order.index("prioritized") + 1, "kmeans_cluster") 
variants = variants[column_order]
variants.to_csv(clustered_variants_loc, sep="\t", index=False)

print("plotting...")
# print(variants["kmeans_cluster"]); 
variants_to_plot = variants[variants["kmeans_cluster"] != "None"]
variants_to_plot = variants_to_plot.sort_values(
    by=["kmeans_cluster"], ascending=(True), ignore_index=True
)
variants_to_plot_scores = np.abs(
    variants_to_plot[[x for x in variants_to_plot.columns if x.startswith("score-")]]
)
variants_to_plot_scores.columns = variants_to_plot_scores.columns.str.replace(
    "score-", "", regex=False
)

# import anndata
# import scanpy as sc
# adata = anndata.AnnData(X=variants_to_plot_scores)
# sc.pl.heatmap(adata, cmap="viridis", show=True)

cluster_cmap = plt.get_cmap("tab20")
cluster_colors = [cluster_cmap(i) for i in range(20)]
cluster_cmap_dark = plt.get_cmap("Dark2")
cluster_colors += [cluster_cmap_dark(i) for i in range(8)]
cluster_cmap_set = plt.get_cmap("Set3")
cluster_colors += [cluster_cmap_set(i) for i in range(12)]
varcluster_color = [cluster_colors[x] for x in list(variants_to_plot["kmeans_cluster"])]

# Create a legend for the cluster colors

unique_clusters = variants_to_plot["kmeans_cluster"].unique()
handles = [Patch(facecolor=cluster_colors[cluster], label=f'Cluster {cluster}') for cluster in unique_clusters]

fig = sns.clustermap(
    variants_to_plot_scores.transpose(),
    row_cluster=True,
    col_cluster=False,
    col_colors=[varcluster_color],
    cbar_pos=(1, 0.2, 0.03, 0.4),
    figsize=(15, 20),
    vmax=4,
    yticklabels=True,
    xticklabels=False,
    dendrogram_ratio=(0.1, 0.2),
)

# Add the legend to the plot
plt.legend(handles=handles, title='Clusters', bbox_to_anchor=(1, 1.5), loc='upper left')

plt.setp(fig.ax_heatmap.get_yticklabels(), fontsize=18)
cluster_plot_loc_ = cluster_plot_loc.replace(".pdf", f"_{i}.pdf")
plt.savefig(cluster_plot_loc_, bbox_inches="tight", format="pdf")
    # plt.show()

import numpy as np
import pandas as pd
from tqdm import tqdm
import umap
import hdbscan
from sklearn.preprocessing import normalize
import warnings
warnings.filterwarnings("ignore")

INPUT_EMBEDDINGS  = "embeddings.npy"
INPUT_METADATA    = "metadata.pkl"
OUTPUT_LABELED    = "videos_clustered.csv"
OUTPUT_SAMPLES    = "cluster_samples.csv"

# UMAP settings
UMAP_N_COMPONENTS = 50
UMAP_N_NEIGHBORS  = 30
UMAP_MIN_DIST     = 0.0

HDBSCAN_MIN_CLUSTER_SIZE = 75
HDBSCAN_MIN_SAMPLES      = 10

SAMPLES_PER_CLUSTER = 10

# Column names
COL_TITLE   = "title"
COL_CHANNEL = "channel"
COL_TAGS    = "tags"
COL_ID      = "video_id"

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Load
    print("Loading embeddings and metadata...")
    embeddings = np.load(INPUT_EMBEDDINGS)
    df = pd.read_pickle(INPUT_METADATA)
    print(f"  {embeddings.shape[0]:,} videos, {embeddings.shape[1]} dimensions\n")

    print(f"Running UMAP (→ {UMAP_N_COMPONENTS} dimensions)...")
    reducer = umap.UMAP(
        n_components=UMAP_N_COMPONENTS,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric="cosine",
        random_state=42,
        verbose=True,
        low_memory=False,
    )
    reduced = reducer.fit_transform(embeddings)
    print(f"UMAP complete. Shape: {reduced.shape}\n")

    print(f"Running HDBSCAN (min_cluster_size={HDBSCAN_MIN_CLUSTER_SIZE})...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",  # "eom" or "leaf" — eom gives bigger clusters
        prediction_data=True,
    )
    labels = clusterer.fit_predict(reduced)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise    = (labels == -1).sum()
    noise_pct  = 100 * n_noise / len(labels)

    print(f"\nFound {n_clusters} clusters")
    print(f"Noise points (unclustered): {n_noise:,} ({noise_pct:.1f}%)")

    df["cluster_id"] = labels
    df["cluster_label"] = df["cluster_id"].apply(
        lambda x: f"Cluster_{x:03d}" if x >= 0 else "UNCLUSTERED"
    )

    df.to_csv(OUTPUT_LABELED, index=False)
    print(f"\nSaved full labeled dataset: {OUTPUT_LABELED}")

    print(f"\nGenerating {SAMPLES_PER_CLUSTER} samples per cluster for review...")
    sample_rows = []

    cluster_sizes = df[df["cluster_id"] >= 0].groupby("cluster_id").size().sort_values(ascending=False)

    for cluster_id, size in cluster_sizes.items():
        cluster_df = df[df["cluster_id"] == cluster_id]
        samples = cluster_df.sample(min(SAMPLES_PER_CLUSTER, len(cluster_df)), random_state=42)

        for _, row in samples.iterrows():
            sample_rows.append({
                "cluster_id":    cluster_id,
                "cluster_size":  size,
                "topic_name":    "",   # fill this in after reviewing
                COL_ID:          row.get(COL_ID, ""),
                COL_TITLE:       row.get(COL_TITLE, ""),
                COL_CHANNEL:     row.get(COL_CHANNEL, ""),
                COL_TAGS:        str(row.get(COL_TAGS, ""))[:100],
            })

    samples_df = pd.DataFrame(sample_rows)
    samples_df.to_csv(OUTPUT_SAMPLES, index=False)


if __name__ == "__main__":
    main()

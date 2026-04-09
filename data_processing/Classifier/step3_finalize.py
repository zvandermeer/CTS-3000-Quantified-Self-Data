import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings("ignore")

INPUT_CLUSTERED   = "videos_clustered.csv"
INPUT_SAMPLES     = "cluster_samples.csv"
INPUT_EMBEDDINGS  = "embeddings.npy"
OUTPUT_FINAL      = "videos_final.csv"

COL_TITLE = "title"
COL_ID    = "video_id"

def main():

    # Load
    df       = pd.read_csv(INPUT_CLUSTERED)
    samples  = pd.read_csv(INPUT_SAMPLES)
    embeddings = np.load(INPUT_EMBEDDINGS)

    mapping = (
        samples[samples["topic_name"].notna() & (samples["topic_name"].str.strip() != "")]
        .groupby("cluster_id")["topic_name"]
        .first()
        .to_dict()
    )

    unnamed = [cid for cid in df["cluster_id"].unique() if cid >= 0 and cid not in mapping]
    if unnamed:
        for cid in unnamed:
            mapping[cid] = f"Unnamed_Cluster_{cid:03d}"

    print(f"Loaded {len(mapping)} named topics\n")

    df["topic"] = df["cluster_id"].map(mapping)

    unclustered_mask = df["cluster_id"] == -1
    n_unclustered = unclustered_mask.sum()

    if n_unclustered > 0:
        print(f"Handling {n_unclustered:,} unclustered videos...")

        cluster_ids = sorted(mapping.keys())
        centroids = {}
        for cid in cluster_ids:
            idx = df[df["cluster_id"] == cid].index
            centroids[cid] = embeddings[idx].mean(axis=0)

        centroid_matrix = np.stack([centroids[cid] for cid in cluster_ids])
        unclustered_idx = df[unclustered_mask].index
        unclustered_embeddings = embeddings[unclustered_idx]

        sims = cosine_similarity(unclustered_embeddings, centroid_matrix)
        best_cluster_pos = sims.argmax(axis=1)
        best_cluster_ids = [cluster_ids[i] for i in best_cluster_pos]
        best_scores      = sims.max(axis=1)

        df.loc[unclustered_idx, "cluster_id"] = best_cluster_ids
        df.loc[unclustered_idx, "topic"]      = [mapping[c] for c in best_cluster_ids]
        df.loc[unclustered_idx, "nearest_cluster_score"] = best_scores
        df.loc[unclustered_idx, "was_unclustered"] = True
    else:
        print("No unclustered videos")

    df["was_unclustered"] = df["was_unclustered"].fillna(False) if "was_unclustered" in df.columns else False

    # ── Save ──────────────────────────────────────────────────────────────────
    output_cols = [COL_ID, COL_TITLE, "topic", "cluster_id", "was_unclustered"] + \
                  [c for c in df.columns if c not in [COL_ID, COL_TITLE, "topic", "cluster_id",
                                                        "was_unclustered", "cluster_label"]]
    df[output_cols].to_csv(OUTPUT_FINAL, index=False)

    print(f"\nSaved final labeled dataset: {OUTPUT_FINAL}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("TOPIC SUMMARY")
    print(f"{'='*60}")
    topic_counts = df.groupby("topic").size().sort_values(ascending=False)
    print(f"{'Topic':<40} {'Count':>8}")
    print("-" * 50)
    for topic, count in topic_counts.items():
        pct = 100 * count / len(df)
        print(f"{str(topic):<40} {count:>8,}  ({pct:.1f}%)")
    print("-" * 50)
    print(f"{'TOTAL':<40} {len(df):>8,}")
    print()


if __name__ == "__main__":
    main()

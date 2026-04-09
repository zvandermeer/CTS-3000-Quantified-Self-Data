import os
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import torch

INPUT_CSV     = "videos.csv"
OUTPUT_EMBEDDINGS = "embeddings.npy"
OUTPUT_METADATA   = "metadata.pkl"

COL_ID       = "video_id"
COL_TITLE    = "title"
COL_TAGS     = "tags"
COL_DESC     = "description"
COL_CHANNEL  = "channel"

MODEL_NAME   = "all-MiniLM-L6-v2"

BATCH_SIZE   = 512
MAX_DESC_CHARS = 200  # Only use first N chars of description

def get_device():
    if torch.backends.mps.is_available():
        # Use Apple MPS as GPU
        return "mps"
    elif torch.cuda.is_available():
        # Use CUDA GPU
        return "cuda"
    else:
        # Use CPU
        return "cpu"

def build_text(row):
    parts = []

    title = str(row.get(COL_TITLE, "")).strip()
    if title:
        parts.append(title)
        parts.append(title)  # weight title more heavily

    tags = str(row.get(COL_TAGS, "")).strip()
    if tags and tags.lower() not in ("nan", "none", ""):
        parts.append(tags)

    desc = str(row.get(COL_DESC, "")).strip()
    if desc and desc.lower() not in ("nan", "none", ""):
        parts.append(desc[:MAX_DESC_CHARS])

    channel = str(row.get(COL_CHANNEL, "")).strip()
    if channel and channel.lower() not in ("nan", "none", ""):
        parts.append(f"Channel: {channel}")

    return " | ".join(parts)

def main():
    # Load data
    print(f"Loading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df):,} videos\n")

    # Build text inputs
    print("Building text inputs...")
    texts = [build_text(row) for _, row in tqdm(df.iterrows(), total=len(df))]

    # Show a sample
    print(f"\nSample text input:\n  {texts[0][:200]}\n")

    # Load model
    device = get_device()
    print(f"\nLoading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME, device=device)

    # Embed
    print(f"\nEmbedding {len(texts):,} videos in batches of {BATCH_SIZE}...")
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    print(f"\nEmbedding shape: {embeddings.shape}")

    # Save
    np.save(OUTPUT_EMBEDDINGS, embeddings)
    df.to_pickle(OUTPUT_METADATA)

    print(f"\nSaved embeddings to: {OUTPUT_EMBEDDINGS}")
    print(f"Saved metadata to:   {OUTPUT_METADATA}")


if __name__ == "__main__":
    main()

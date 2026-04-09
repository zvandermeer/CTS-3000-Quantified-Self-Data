import time
import json
import requests
import pandas as pd
import numpy as np

YOUTUBE_API_KEY = "AIzaSyC8J2W7KDOlIjpj__cAVwRWvMOAzTetO7Y"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"

def get_metadata(series: pd.Series) -> list[dict]:
    params = {
        "part": "contentDetails,id,liveStreamingDetails,paidProductPlacementDetails,recordingDetails,snippet,statistics,topicDetails",
        "id": ",".join(series),
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url=YOUTUBE_API_URL, params=params)
    response.raise_for_status()
    data = response.json()

    return data["items"]

def main():
    with open("watch-history.csv", 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)

    print("Processing video IDs...")
    video_ids: pd.Series = df['video_url'].str.split("v=").str[1].str.split("&").str[0]
    video_ids: pd.Series = video_ids.dropna()

    results: list[dict] = []

    counter = 0

    startAt = 20

    n = 50
    for g, series in video_ids.groupby(np.arange(len(video_ids)) // n):
        counter += 1
        if (counter < startAt):
            print(f"Skipping batch {counter}")
            continue

        print(f"Running batch... ({counter}/1551)")
        result = get_metadata(series)
        results.extend(result)

        with open("allData.json", 'a', encoding='utf-8') as f:
            thisdata = json.dumps(result, ensure_ascii=False)

            f.write(thisdata+"\n")

        time.sleep(0.25)

    print("Writing data...")

    print("Done!")

if __name__ == "__main__":
    main()
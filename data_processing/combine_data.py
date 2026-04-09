import json
import pandas as pd

def main():
    with open("categories.json", 'r', encoding='utf-8') as f:
        data = json.load(f)["items"]

    data = pd.json_normalize(data)

    categories = data.set_index("id")["snippet.title"]

    with open("allData-combined.json", 'r', encoding='utf-8') as f:
        data = json.load(f)

    json_data = pd.json_normalize(data)

    json_data["category_name"] = json_data["snippet.categoryId"].map(categories)

    json_data = json_data.drop_duplicates("id").set_index("id")

    video_length = pd.to_timedelta(
        json_data["contentDetails.duration"],
        errors="coerce"
    ).dt.total_seconds().astype("Int64")

    youtube_category = json_data["category_name"]

    with open("videos_final.csv", 'r', encoding='utf-8') as f:
        ml_data = pd.read_csv(f)

    video_category = ml_data.drop_duplicates("video_id").set_index("video_id")["topic"]

    with open("new-watch-history.csv", 'r', encoding='utf-8') as f:
        csv_data = pd.read_csv(f)

    # csv_data = csv_data.set_index("video_id")

    csv_data["video_length"] = csv_data["video_id"].map(video_length)
    csv_data["video_category"] = csv_data["video_id"].map(video_category)
    csv_data["youtube_category"] = csv_data["video_id"].map(youtube_category)

    with open("final-watch-history3.csv", 'w', encoding='utf-8') as f:
        csv_data.to_csv(f,index=False)

main()
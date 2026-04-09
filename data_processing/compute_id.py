import pandas as pd

def main():
    with open("watch-history.csv", 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)

    print("Computing video IDs...")
    df["video_id"] = df['video_url'].str.split("v=").str[1].str.split("&").str[0]
    df = df.dropna(subset=["video_id"])

    with open('new-watch-history.csv', 'w', encoding='utf-8') as f:
        df.to_csv(f,index=False)

main()
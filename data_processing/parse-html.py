from datetime import datetime
from lxml.etree import _Element
from lxml import etree
import pandas as pd


def extract_content_cells(filepath: str) -> list[etree._Element]:
    results: list[etree._Element] = []
    context = etree.iterparse(filepath, html=True, events=("end",), tag="div", encoding='utf-8')

    for _, elem in context:
        if "outer-cell" in elem.get("class", ""):
            results.append(elem)

    return results

def parse_watch_history_cell(element: _Element) -> dict:
    # Find all <a> tags inside the correct content-cell
    content_cell = element.find('.//*[@class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1"]')
    
    if not isinstance(content_cell, _Element):
        return {}

    links = content_cell.findall('.//a')

    date_str = content_cell.findall('.//br')[-2].tail.strip()
    
    date = datetime.strptime(date_str, '%b %d, %Y, %I:%M:%S\u202f%p %Z')

    if len(links) < 2:
        return {}

    return {
        'video_title': links[0].text,
        'video_url': links[0].get('href'),
        'channel_name': links[1].text,
        'channel_url': links[1].get('href'),
        'date': date
    }

def parse_search_history_cell(element: _Element) -> dict:
    content_cell = element.find('.//*[@class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1"]')
    
    if not isinstance(content_cell, _Element):
        return {}

    links = content_cell.findall('.//a')

    date_str = content_cell.findall('.//br')[-2].tail.strip()
    
    date = datetime.strptime(date_str, '%b %d, %Y, %I:%M:%S\u202f%p %Z')

    return {
        'search_term': links[0].text,
        'date': date
    }

def main():
    # replace "watch" with "search" to extract search history
    INPUT_FILE = "Takeout/Youtube and Youtube Music/history/watch-history.html"
    OUTPUT_FILE = "watch-history.csv"

    print(f"Extracting content from {INPUT_FILE}...")

    divs = extract_content_cells(
        INPUT_FILE
    )

    results: list[dict] = []

    print("Processing pages...")

    # Usage
    for div in divs:
        # replace "watch" with "search" to compute search history
        result = parse_watch_history_cell(div)
        if not result == {}:
            results.append(result)

    print(f"Saving results to {OUTPUT_FILE}...")

    df = pd.DataFrame(results)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        df.to_csv(f,index=False)

    print("Done!")

if __name__ == "__main__":
    main()

import json

final_array = []

with open("allData.json", 'r', encoding='utf-8') as f:
    for line in f:
        array = json.loads(line)
        final_array.extend(array)

with open("allData-combined.json", 'w', encoding='utf-8') as f:
    json.dump(final_array, f)

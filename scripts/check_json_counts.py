
import json
import os

input_file = "data_backup.json"
if not os.path.exists(input_file):
    print("File not found")
else:
    with open(input_file, "r") as f:
        data = json.load(f)
    
    for key in data:
        print(f"{key}: {len(data[key])}")

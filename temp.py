import json

# Read the JSON file
with open("quiz_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Remove the 'answer' key from each dictionary in the list
for item in data:
    if "answer" in item:
        del item["answer"]

# Save the modified data back to the file
with open("new_quiz_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
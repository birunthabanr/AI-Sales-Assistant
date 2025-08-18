import json
import pandas as pd
from pathlib import Path

# ====== CONFIG ======
dataset_split = "dev"  # or "dev"
base_path = Path("C:/Users/Udarata Computers/OneDrive/Desktop/AI-Sales-Assistant/Data") # Adjust this path as needed
schema_file = base_path / dataset_split / "schema.json"
dialogue_folder = base_path / dataset_split
output_csv = f"dstc8_{dataset_split}_utterances_intents.csv"

# ====== LOAD SCHEMA ======
with open(schema_file, "r", encoding="utf-8") as f:
    schema = json.load(f)

# Collect all intents for reference
all_intents = []
for service in schema:
    for intent in service.get("intents", []):
        all_intents.append(intent["name"])
print(f"Found {len(all_intents)} intents in schema.")

# ====== PARSE DIALOGUES ======
texts = []
labels = []

for dialogue_file in dialogue_folder.glob("dialogues_*.json"):
    with open(dialogue_file, "r", encoding="utf-8") as f:
        dialogues = json.load(f)

    for dialog in dialogues:
        for turn in dialog["turns"]:
            if turn["speaker"] != "USER":
                continue

            utterance = turn["utterance"]
            intent = "unknown"

            for frame in turn.get("frames", []):
                active_intent = frame.get("state", {}).get("active_intent", "NONE")
                if active_intent != "NONE":
                    intent = active_intent
                    break

            if intent != "unknown" and intent != "NONE":
                texts.append(utterance)
                labels.append(intent)

# ====== SAVE TO CSV ======
df = pd.DataFrame({"text": texts, "label": labels})
df.to_csv(output_csv, index=False, encoding="utf-8")
print(f"Saved {len(df)} utterances with intents to {output_csv}")
print("Example:")
print(df.head())

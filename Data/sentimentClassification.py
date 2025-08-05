import json
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from tqdm import tqdm

# Load JSON data (list of dialogues)
with open("Data/output/dialogues_events.json", "r", encoding="utf-8") as f:
    dialogues = json.load(f)

# Load the pretrained sentiment model
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
model.eval()

# Map numeric output to sentiment labels
labels = ['negative', 'neutral', 'positive']

# Classify a single utterance
def classify_sentiment(text):
    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
        scores = F.softmax(outputs.logits, dim=1)
        predicted_label = torch.argmax(scores).item()
        return labels[predicted_label]
    except Exception as e:
        print(f"Error processing: {text}")
        return "neutral"

# Extract and label all utterances
rows = []

for dialogue in tqdm(dialogues, desc="Processing Dialogues"):
    for turn in dialogue.get("turns", []):
        text = turn.get("utterance", "")
        speaker = turn.get("speaker", "UNKNOWN")
        if not text.strip():
            continue  # Skip empty
        sentiment = classify_sentiment(text)
        rows.append({"text": text, "speaker": speaker, "label": sentiment})

# Create and save DataFrame
df = pd.DataFrame(rows)
df.to_csv("Data/auto_labeled_sentiment_dataset.csv", index=False)
# Display the first few rows of the DataFrame
print(df.head())
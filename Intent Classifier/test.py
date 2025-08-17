import pandas as pd
import torch
from torch.utils.data import DataLoader
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import pickle
from sklearn.metrics import classification_report

# ===== Load model and tokenizer =====
model = DistilBertForSequenceClassification.from_pretrained("./distilbert-dstc8-intent")
tokenizer = DistilBertTokenizer.from_pretrained("./distilbert-dstc8-intent")

# Load label encoder
with open("label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# ===== Load test CSV =====
test_df = pd.read_csv("../Data/dstc8_test_utterances_intents.csv")

# Filter out unseen labels
known_labels = set(label_encoder.classes_)
test_df = test_df[test_df["label"].isin(known_labels)].copy()

if test_df.empty:
    raise ValueError("No test samples match the training labels! Check dataset consistency.")

# Encode labels
test_df["label_id"] = label_encoder.transform(test_df["label"])

# ===== TOKENIZE =====
test_encodings = tokenizer(
    test_df["text"].tolist(),
    truncation=True,
    padding=True,
    max_length=64
)

class IntentDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

test_dataset = IntentDataset(test_encodings, test_df["label_id"].tolist())
test_loader = DataLoader(test_dataset, batch_size=16)

# ===== EVALUATE =====
all_preds = []
all_labels = []

with torch.no_grad():
    for batch in test_loader:
        labels = batch["labels"].to(device)
        inputs = {k: v.to(device) for k, v in batch.items() if k != "labels"}
        outputs = model(**inputs)
        preds = torch.argmax(outputs.logits, dim=-1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

# ===== METRICS =====
accuracy = (torch.tensor(all_preds) == torch.tensor(all_labels)).float().mean().item()
print(f"\nTest Accuracy: {accuracy:.4f}")

# Detailed classification report
report = classification_report(
    all_labels,
    all_preds,
    target_names=label_encoder.classes_
)
print("\nClassification Report:\n", report)

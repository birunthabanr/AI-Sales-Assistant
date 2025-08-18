import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, get_scheduler
from torch.optim import AdamW
from tqdm import tqdm
import pickle

# ====== LOAD DATA ======
df = pd.read_csv("./Data/dstc8_train_utterances_intents.csv")

# Encode labels
label_encoder = LabelEncoder()
df["label_id"] = label_encoder.fit_transform(df["label"])
num_labels = len(label_encoder.classes_)

# Train/validation split
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["text"].tolist(),
    df["label_id"].tolist(),
    test_size=0.1,
    random_state=42,
    stratify=df["label_id"]
)

# ====== TOKENIZER ======
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=64)
val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=64)

# ====== DATASET CLASS ======
class IntentDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = IntentDataset(train_encodings, train_labels)
val_dataset = IntentDataset(val_encodings, val_labels)

# ====== MODEL ======
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=num_labels
)

# ====== TRAINING SETUP ======
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
model.to(device)

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True) 
val_loader = DataLoader(val_dataset, batch_size=16) 

optimizer = AdamW(model.parameters(), lr=5e-5)
num_training_steps = len(train_loader) * 1  # 1 epoch
lr_scheduler = get_scheduler("linear", optimizer=optimizer, num_warmup_steps=0, num_training_steps=num_training_steps)

# ====== TRAIN LOOP ======
for epoch in range(1):
    model.train()
    loop = tqdm(train_loader, desc=f"Epoch {epoch+1}")
    for batch in loop:
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)
        loss = outputs.loss

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        lr_scheduler.step()

        loop.set_postfix(loss=loss.item())

    # ====== VALIDATION ======
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for batch in val_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            preds = torch.argmax(outputs.logits, dim=-1)
            correct += (preds == batch["labels"]).sum().item()
            total += batch["labels"].size(0)
    accuracy = correct / total
    print(f"Validation Accuracy: {accuracy:.4f}")

# ====== SAVE MODEL ======
model.save_pretrained("./distilbert-dstc8-intent")
tokenizer.save_pretrained("./distilbert-dstc8-intent")

# ====== SAVE LABEL ENCODER ======
with open("label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)

print("Model and tokenizer saved to ./distilbert-dstc8-intent")

import os
import json
import re
from collections import defaultdict

# Paths
DATASET_PATH = "train"
SCHEMA_FILE = os.path.join(DATASET_PATH, "schema.json")
OUTPUT_DIR = "output"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Extract domains from schema
with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
    schema = json.load(f)

domains = set()
for service in schema:
    service_name = service.get("service_name", "")
    match = re.match(r"([A-Za-z]+)", service_name)
    if match:
        domain = match.group(1).lower()
        domains.add(domain)

print("Identified domains:")
for domain in sorted(domains):
    print("-", domain)
print(f"Total: {len(domains)}\n")

# Prepare storage for dialogues per domain
domain_dialogues = defaultdict(list)
seen_dialogue_ids = set()  # Optional: if dialogues have unique IDs

# Iterate over dialogue files and assign each dialogue to ONE domain
for filename in os.listdir(DATASET_PATH):
    if filename.endswith(".json") and filename != "schema.json":
        file_path = os.path.join(DATASET_PATH, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            dialogues = json.load(f)
            for dlg in dialogues:
                services = dlg.get("services", [])
                assigned = False
                for service in services:
                    match = re.match(r"([A-Za-z]+)", service)
                    if match:
                        domain = match.group(1).lower()
                        if domain in domains:
                            # Optional: skip if already processed
                            dlg_id = id(dlg)  # use a unique hash if available
                            if dlg_id not in seen_dialogue_ids:
                                domain_dialogues[domain].append(dlg)
                                seen_dialogue_ids.add(dlg_id)
                            assigned = True
                            break  # Only assign to one domain
                if not assigned:
                    continue  # Skip if no domain matched

# Save to compact JSON files
for domain, dialogues in domain_dialogues.items():
    output_file = os.path.join(OUTPUT_DIR, f"dialogues_{domain}.json")
    with open(output_file, "w", encoding="utf-8") as f_out:
        # Compact format: no indent, no extra whitespace
        json.dump(dialogues, f_out, separators=(",", ":"))
    print(f"Saved {len(dialogues)} dialogues to {output_file}")

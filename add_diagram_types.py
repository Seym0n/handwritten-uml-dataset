"""
Script to add "type" field to each annotation in annotations.json.
- Images from folders containing "activity_diagram" -> "activity_diagram"
- All others -> "class_diagram"
"""
import json
from pathlib import Path

ANNOTATIONS_FILE = "annotations.json"

def infer_type(image_path: str) -> str:
    path = Path(image_path)
    for part in path.parts:
        if "activity_diagram" in part.lower() or "activity" in part.lower():
            return "activity_diagram"
    return "class_diagram"

with open(ANNOTATIONS_FILE, "r") as f:
    annotations = json.load(f)

for entry in annotations:
    if "type" not in entry:
        entry["type"] = infer_type(entry["image"])

with open(ANNOTATIONS_FILE, "w") as f:
    json.dump(annotations, f, indent=2)

# Print summary
counts = {}
for entry in annotations:
    t = entry["type"]
    counts[t] = counts.get(t, 0) + 1

print(f"Done. Updated {len(annotations)} annotations:")
for t, c in counts.items():
    print(f"  {t}: {c}")

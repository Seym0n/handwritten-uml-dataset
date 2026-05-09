import json
from collections import Counter
from pathlib import Path

with open("annotations.json", "r") as f:
    annotations = json.load(f)

total = len(annotations)
counts = Counter(entry.get("type", "unknown") for entry in annotations)

print(f"Total annotations: {total}")
print()
for diagram_type, count in sorted(counts.items()):
    pct = count / total * 100 if total else 0
    print(f"  {diagram_type}: {count} ({pct:.1f}%)")

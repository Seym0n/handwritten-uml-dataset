"""
Pre-check all annotations to identify which ones will fail XMI generation.
This avoids hanging during the main processing.
"""
import json
import re

# Load annotations
with open("annotations.json", "r") as f:
    data = json.load(f)

print(f"Checking {len(data)} annotations for association class syntax...")
print("="*60)

association_class_pattern = r'\([^)]+\)\s*\.\.'
problematic_indices = []

for idx, item in enumerate(data):
    # Quick check for association class syntax
    if re.search(association_class_pattern, item['plantuml']):
        problematic_indices.append(idx)
        print(f"Entry {idx+1}: {item['image']} - HAS ASSOCIATION CLASS (will skip)")

print("="*60)
print(f"\nSummary:")
print(f"Total annotations: {len(data)}")
print(f"Will skip due to association classes: {len(problematic_indices)}")
print(f"Will process: {len(data) - len(problematic_indices)}")
print(f"\nProblematic entries: {problematic_indices[:20]}..." if len(problematic_indices) > 20 else f"\nProblematic entries: {problematic_indices}")

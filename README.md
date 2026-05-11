# CAS2UML Validator Tool

A data annotation tool for manually annotating handwritten UML diagrams with PlantUML code, and a pipeline to publish the resulting dataset to HuggingFace.

## Overview

The CAS2UML Validator presents handwritten UML class and activity diagram images one by one in a Gradio web app. For each image, you write the corresponding PlantUML code, which is rendered locally for a live preview. Annotations are saved to `annotations.json` and can be pushed to HuggingFace as a structured dataset.

## Get Started

```bash
pip install -r requirements.txt
python app.py
```

Requires Java to be installed (used for local PlantUML rendering via `plantuml-custompipe-v3.jar`).

## Folder Structure

```
handwritten-uml-dataset/
├── images/
│   ├── activity_diagram1/   # Handwritten scanned activity diagrams
│   ├── activity_diagram2/   # Extra handwritten scanned activity diagrams
│   ├── activity_diagram3/   # Synthetic scanned activity diagrams
│   ├── activity_diagram4/   # Tablet activity diagrams
│   ├── class_diagram1/      # Kaggle handwritten class diagrams
│   ├── class_diagram2/      # Handwritten scanned class diagrams
│   ├── class_diagram3/      # Extra handwritten scanned class diagrams
│   ├── class_diagram4/      # Tablet class diagrams
│   └── class_diagram5/      # Tablet class diagrams v2 (cropped)
├── lindholmen_dataset/
│   └── lindholmen_notebook.ipynb  # Processing of the Lindholmen UML dataset
├── temp/
│   └── Temporary PlantUML preview images (safe to delete contents)
├── app.py                   # Gradio annotation web app
├── plantuml_server.py       # Persistent PlantUML process for XMI generation
├── plantuml-custompipe-v3.jar  # Custom PlantUML JAR with pipe error handling
├── annotations.json         # All annotated images with their PlantUML code
├── hf_pusher.ipynb          # Pushes annotations to HuggingFace as a dataset
├── crop_images.ipynb        # Crops tablet images to remove excess background
├── convert_crop.ipynb       # Converts PDF scans to cropped images
├── annotation_stats.py      # Statistics on the class diagram & activity diagram distribution
├── requirements.txt         # Python dependencies
└── .gitignore
```

## CAS2UML Dataset

The annotated dataset (CAS2UML) is published on HuggingFace:
[Seym0n/handwritten_plantuml_dataset](https://huggingface.co/datasets/Seym0n/handwritten_plantuml_dataset)

It contains handwritten UML class and activity diagram images paired with their PlantUML and XMI representations, split into train/test sets.

## PlantUML JAR

The `plantuml-custompipe-v3.jar` is not stored in this repository due to its size. Download it from the [Releases page](../../releases) and place it in the root directory.

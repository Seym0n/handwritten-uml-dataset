# CAS2UML Validator Tool

A data annotation tool for manually annotating handwritten UML diagrams with PlantUML code, and a pipeline to publish the resulting dataset to HuggingFace.

## Overview

The CAS2UML Validator presents handwritten UML class and activity diagram images one by one in a Gradio web app. For each image, you write the corresponding PlantUML code in a text editor, which is rendered locally for a live preview. This setup allows one to iteratively edit the PlantUML code while checking the rendered diagram against the handwritten original. Annotations are saved to `annotations.json` and can be pushed to HuggingFace as a structured dataset.

`annotations.json` in this repository already contains the full set of annotations for the released dataset (see [CAS2UML Dataset](#cas2uml-dataset) below). The annotation tool itself is meant for previewing, extending the dataset with new images or correcting existing labels.

## Requirements

- Python 3.10+
- Java 11+ (JRE or JDK), used for local PlantUML rendering via `plantuml-custompipe-v3.jar` — see [PlantUML JAR](#plantuml-jar) below

## Get Started

```bash
python3 -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:7860 in a browser.

`requirements.txt` only installs what `app.py` needs (just `gradio`). The `.ipynb` notebooks (cropping, PDF conversion, HuggingFace push) have their own, much heavier dependencies (e.g. `torch`, `pdf2image`); install those separately only if you need to run a notebook:

```bash
pip install -r requirements-notebooks.txt
```

### Navigating images

Use **← Previous** / **Next →** to step through images one at a time, or type a number into **Jump to image #** and press **Go** to go directly to any image in the set (there are 500+ images, so jumping is the fastest way to reach a specific one). Enable **Skip already labeled data** to have Previous/Next skip over images that already have a saved annotation.

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
├── validate_annotations.py # Validates that all annotations parse/compile with PlantUML
├── requirements.txt         # Python dependencies to run app.py
├── requirements-notebooks.txt  # Extra dependencies needed only by the .ipynb notebooks
└── .gitignore
```

## CAS2UML Dataset

The annotated dataset (CAS2UML) is published on HuggingFace:
[Seym0n/handwritten_plantuml_dataset](https://huggingface.co/datasets/Seym0n/handwritten_plantuml_dataset)

It contains handwritten UML class and activity diagram images paired with their PlantUML and XMI representations, split into train/test sets. This is the same data as `annotations.json`/`images/` in this repo, packaged for direct use with the `datasets` library — you do not need to run the annotation tool to use it.

Load it directly with the [`datasets`](https://huggingface.co/docs/datasets) library:

```python
from datasets import load_dataset

dataset = load_dataset("Seym0n/handwritten_plantuml_dataset")
example = dataset["train"][0]

example["image"]  # PIL.Image of the handwritten diagram
example["code"]   # ground-truth PlantUML code
example["xmi"]    # ground-truth XMI representation
example["type"]   # "class_diagram" or "activity_diagram"
```

This is independent of the annotation tool in this repo — the Gradio app (`app.py`) and `annotations.json` are how the dataset was *produced*; the HuggingFace dataset is the published, ready-to-use *result*. Use `hf_pusher.ipynb` if you want to see how `annotations.json` was converted into this HuggingFace dataset, or to push your own extended annotations.

## PlantUML JAR

The `plantuml-custompipe-v3.jar` is not stored in this repository due to its size. Download it from the [Releases page](../../releases) and place it in the root directory.

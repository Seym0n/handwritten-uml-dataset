# Data Annotation Tool

This is the folder of the data annotation tool used to manually annotate PlantUML code given handwritten UML class diagram and activity diagram sketches.

## Get Started

To open the web app `app.py`, the Python library `gradio` is needed. This can be installed using `pip install gradio`

## Folder Structure

```
data_annotation_tool/
├── images/
│   └── Location of handwritten UML class diagrams
├── temp/
│   └── Temporary images of PlantUML diagrams - contents of folder can be deleted safely (do not delete folder itself)
├── app.py
│   └── Main Gradio web application for annotating diagrams
├── annotations.json
│   └── Annotated handwritten UML class diagrams with their respective PlantUML code
├── hf_pusher.ipynb
│   └── Notebook to transform annotations.json into OpenAI's ChatML format, necessary to push the dataset to HuggingFace dataset, which can be found here: https://huggingface.co/datasets/Seym0n/handwritten_plantuml_dataset (currently private)
└── .gitignore
    └── Git ignore file for version control
```
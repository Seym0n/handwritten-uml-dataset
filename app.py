import gradio as gr
import json
import os
import re
import subprocess
import uuid
from pathlib import Path
from datetime import datetime

# Load/save annotations
ANNOTATIONS_FILE = "annotations.json"
JAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plantuml-custompipe-v3.jar")
_PLANTUML_ERROR_RX = re.compile(r"ERROR\r?\n(\d+)\r?\n([^\r\n]+)")

def normalize_path(path):
    return path.replace("\\", "/") if path else path

def load_annotations():
    if Path(ANNOTATIONS_FILE).exists():
        with open(ANNOTATIONS_FILE, 'r') as f:
            annotations = json.load(f)
        for a in annotations:
            a["image"] = normalize_path(a["image"])
        return annotations
    return []

DIAGRAM_TYPES = ["class_diagram", "activity_diagram"]

def save_annotation(image_path, plantuml_code, diagram_type, annotations):
    image_path = normalize_path(image_path)
    # Check if annotation for this image already exists
    existing_idx = next((i for i, a in enumerate(annotations) if a["image"] == image_path), None)

    annotation_entry = {
        "image": image_path,
        "plantuml": plantuml_code,
        "type": diagram_type,
        "timestamp": datetime.now().isoformat()
    }

    if existing_idx is not None:
        # Update existing annotation
        annotations[existing_idx] = annotation_entry
    else:
        # Add new annotation
        annotations.append(annotation_entry)

    with open(ANNOTATIONS_FILE, 'w') as f:
        json.dump(annotations, f, indent=2)
    return annotations

def render_diagram(puml_code: str):
    """
    Render PlantUML to PNG using local JAR.
    Returns: (image_path, status_message)
    """
    if not puml_code.strip():
        return None, "⚠️ Empty code"

    # Strip markdown fences
    code = puml_code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines).strip()

    # Ensure proper tags
    if "@startuml" not in code and "@startmindmap" not in code:
        code = f"@startuml\n{code}\n@enduml"

    # Extract between @startuml and @enduml
    start_idx = code.find("@startuml")
    end_idx = code.find("@enduml") + len("@enduml")
    code = code[start_idx:end_idx]

    try:
        result = subprocess.run(
            ["java", "-jar", JAR_PATH, "-pipe", "-tpng", "-timeout", "20"],
            input=code.encode("utf-8"),
            capture_output=True,
            timeout=25,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            match = _PLANTUML_ERROR_RX.search(stderr)
            if match:
                cause, line = match.group(2), match.group(1)
                error_msg = f"{cause} (line {line})"
            else:
                error_msg = stderr.strip() or str(result.returncode)
            return None, f"❌ {error_msg}"

        if not result.stdout:
            return None, "❌ No output generated"

        Path("temp").mkdir(exist_ok=True)
        file_name = f"temp/temp_{uuid.uuid4().hex}.png"
        with open(file_name, "wb") as f:
            f.write(result.stdout)

        return file_name, "✅ Valid PlantUML"

    except subprocess.TimeoutExpired:
        return None, "❌ Timeout — diagram too complex?"
    except FileNotFoundError:
        return None, "❌ Java not found — is Java installed?"
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

# Get list of images to annotate
images_to_annotate = list(Path("images").glob("**/*.png")) + list(Path("images").glob("**/*.jpg")) + list(Path("images").glob("**/*.bmp"))
images_to_annotate.sort()

if not images_to_annotate:
    print("⚠️ No images found in 'images' folder! Creating dummy list...")
    images_to_annotate = [None]

# Load existing annotations and check if first image has annotation
loaded_annotations = load_annotations()
first_image_path = normalize_path(str(images_to_annotate[0])) if images_to_annotate[0] else None
existing_annotation = next((a for a in loaded_annotations if a["image"] == first_image_path), None)
initial_code = existing_annotation["plantuml"] if existing_annotation else "```plantuml\n@startuml\n\n\n@enduml\n```"
initial_diagram_type = existing_annotation.get("type", "class_diagram") if existing_annotation else "activity_diagram"
initial_preview, initial_status = render_diagram(initial_code) if existing_annotation else (None, "")

with gr.Blocks(title="UML to PlantUML Annotator") as demo:
    gr.Markdown("# 🎨 UML Diagram → PlantUML Annotation Tool")
    gr.Markdown("Convert handwritten UML diagrams to PlantUML code with live preview")
    
    annotations_state = gr.State(loaded_annotations)
    index_state = gr.State(0)

    with gr.Row():
        # Left: Original UML image
        with gr.Column(scale=1):
            gr.Markdown("### 📷 Original Handwritten UML")
            input_image = gr.Image(
                value=str(images_to_annotate[0]) if images_to_annotate[0] else None,
                label="UML Diagram",
                type="filepath",
            )

            image_path_display = gr.Textbox(
                value=str(images_to_annotate[0]) if images_to_annotate[0] else "",
                label="Current Image Path",
                interactive=False,
                scale=1
            )

            with gr.Row():
                prev_btn = gr.Button("← Previous", size="sm", scale=1)
                progress_text = gr.Textbox(
                    value=f"1 / {len(images_to_annotate)}",
                    label="Progress",
                    interactive=False,
                    scale=1
                )
                next_btn = gr.Button("Next →", size="sm", scale=1)

            with gr.Row():
                jump_input = gr.Number(
                    label="Jump to image #",
                    value=1,
                    precision=0,
                    minimum=1,
                    maximum=len(images_to_annotate),
                    scale=2
                )
                jump_btn = gr.Button("Go", size="sm", scale=1)

            skip_labeled_checkbox = gr.Checkbox(
                label="Skip already labeled data",
                value=False,
                info="When enabled, navigation will skip images that have already been annotated"
            )
        
        # Right: PlantUML code and preview
        with gr.Column(scale=1):
            gr.Markdown("### 💻 PlantUML Code")
            plantuml_editor = gr.TextArea(
                label="PlantUML Code",
                lines=12,
                value=initial_code,
                placeholder="Write your PlantUML code here..."
            )

            diagram_type_dropdown = gr.Dropdown(
                choices=DIAGRAM_TYPES,
                value=initial_diagram_type,
                label="Diagram Type",
            )

            status = gr.Textbox(label="Status", interactive=False, scale=1, value=initial_status)

            with gr.Row():
                validate_btn = gr.Button("🔄 Update Preview", variant="secondary", scale=1)
                save_btn = gr.Button("💾 Save Annotation", variant="primary", scale=1)
            
            gr.Markdown("### 👁️ Live Preview")
            preview_image = gr.Image(label="PlantUML Preview", value=initial_preview)
    
    # Statistics
    with gr.Row():
        stats = gr.Markdown(f"**📊 Annotated: {len(loaded_annotations)} / {len(images_to_annotate)}**")
    
    
    def update_preview(code):
        img_path, status_msg = render_diagram(code)
        return img_path, status_msg
    
    def save_current(current_idx, code, diagram_type, annotations):
        # Use the original image path from images_to_annotate list, not from Gradio
        original_image_path = str(images_to_annotate[current_idx]) if images_to_annotate[current_idx] else None

        if not original_image_path:
            return annotations, "❌ No image selected", stats.value

        annotations = save_annotation(original_image_path, code, diagram_type, annotations)
        annotated_count = len(annotations)
        return (
            annotations,
            f"✅ Saved! ({annotated_count} / {len(images_to_annotate)} completed)",
            f"**📊 Annotated: {annotated_count} / {len(images_to_annotate)}**"
        )
    
    def navigate(direction, current_idx, annotations, skip_labeled=False):
        new_idx = current_idx + direction
        new_idx = max(0, min(new_idx, len(images_to_annotate) - 1))

        # If skip_labeled is enabled, keep moving in the direction until we find an unlabeled image
        if skip_labeled:
            attempts = 0
            max_attempts = len(images_to_annotate)

            while attempts < max_attempts:
                new_image = normalize_path(str(images_to_annotate[new_idx])) if images_to_annotate[new_idx] else None
                existing = next((a for a in annotations if a["image"] == new_image), None)

                # If no existing annotation, we found an unlabeled image
                if not existing:
                    break

                # Move to next image in the direction
                new_idx = new_idx + direction

                # Check bounds - if we've reached the edge, stay at current position
                if new_idx >= len(images_to_annotate) or new_idx < 0:
                    # Reached the boundary - stay at current position since no unlabeled images found
                    new_idx = current_idx
                    break

                attempts += 1

        return load_index(new_idx, annotations)

    def load_index(new_idx, annotations):
        new_image = str(images_to_annotate[new_idx]) if images_to_annotate[new_idx] else None
        new_image_key = normalize_path(new_image)

        # Check if this image already has annotation
        existing = next((a for a in annotations if a["image"] == new_image_key), None)
        code = existing["plantuml"] if existing else "```plantuml\n@startuml\n\n\n@enduml\n```"
        diagram_type = existing.get("type", "class_diagram") if existing else "activity_diagram"

        # Also update preview
        preview_img, status_msg = render_diagram(code)

        return (
            new_image,
            code,
            diagram_type,
            new_idx,
            f"{new_idx + 1} / {len(images_to_annotate)}",
            preview_img,
            status_msg,
            new_image if new_image else ""
        )

    def jump_to(image_number, annotations):
        new_idx = int(image_number) - 1
        new_idx = max(0, min(new_idx, len(images_to_annotate) - 1))
        return load_index(new_idx, annotations)

    # Event handlers
    validate_btn.click(
        update_preview,
        inputs=[plantuml_editor],
        outputs=[preview_image, status]
    )
    
    save_btn.click(
        save_current,
        inputs=[index_state, plantuml_editor, diagram_type_dropdown, annotations_state],
        outputs=[annotations_state, status, stats]
    )

    next_btn.click(
        lambda idx, ann, skip: navigate(1, idx, ann, skip),
        inputs=[index_state, annotations_state, skip_labeled_checkbox],
        outputs=[input_image, plantuml_editor, diagram_type_dropdown, index_state, progress_text, preview_image, status, image_path_display]
    )

    prev_btn.click(
        lambda idx, ann, skip: navigate(-1, idx, ann, skip),
        inputs=[index_state, annotations_state, skip_labeled_checkbox],
        outputs=[input_image, plantuml_editor, diagram_type_dropdown, index_state, progress_text, preview_image, status, image_path_display]
    )

    jump_btn.click(
        jump_to,
        inputs=[jump_input, annotations_state],
        outputs=[input_image, plantuml_editor, diagram_type_dropdown, index_state, progress_text, preview_image, status, image_path_display]
    )

if __name__ == "__main__":
    # Create images folder if it doesn't exist
    Path("images").mkdir(exist_ok=True)
    
    demo.launch(share=False)
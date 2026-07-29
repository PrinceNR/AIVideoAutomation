from pathlib import Path

from presentation.template_loader import TemplateLoader


loader = TemplateLoader()

presentation = loader.load(
    Path("templates/vocabulary_template_v1.pptx")
)

print("Presentation loaded successfully!")

print(f"Slides: {len(presentation.slides)}")
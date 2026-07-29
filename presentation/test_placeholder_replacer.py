from pathlib import Path

from presentation.template_loader import TemplateLoader
from presentation.placeholder_replacer import PlaceholderReplacer


loader = TemplateLoader()
presentation = loader.load(
    Path("templates/vocabulary_template_v2.pptx")
)

replacer = PlaceholderReplacer()

replacer.replace_text(
    presentation,
    "{{WORD}}",
    "Algorithm"
)

presentation.save(
    "output/test_placeholder.pptx"
)

print("Placeholder replaced successfully!")
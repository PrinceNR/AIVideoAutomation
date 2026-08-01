from presentation.template_loader import TemplateLoader
from presentation.slide_duplicator import SlideDuplicator
from presentation.image_replacer import ImageReplacer
from pathlib import Path

loader = TemplateLoader()
duplicator = SlideDuplicator()
replacer = ImageReplacer()

# presentation = loader.load("templates/vocabulary_template_v2.pptx")
presentation = loader.load(
    Path("templates/vocabulary_template_v2.pptx")
)

# Duplicate all 4 slides
for i in range(4):
    duplicator.duplicate_slide(presentation, i)

print("Slides:", len(presentation.slides))

# Try replacing ONLY the picture on Slide 8 (index 7)
replacer.replace_image(
    presentation.slides[7],
    Path("output/electronics/images/circuit/001.jpg")
)

presentation.save("test_duplicate_picture.pptx")
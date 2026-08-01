from pathlib import Path

from presentation.template_loader import TemplateLoader
from presentation.slide_group_duplicator import SlideGroupDuplicator


loader = TemplateLoader()
duplicator = SlideGroupDuplicator()

presentation = loader.load(
    Path("templates/vocabulary_template_v2.pptx")
)

print("Before:", len(presentation.slides))

new_slides = duplicator.duplicate_group(
    presentation,
    start_slide=0,
    slide_count=4
)

print("Duplicated:", len(new_slides))
print("After:", len(presentation.slides))

presentation.save(
    Path("output/test_slide_group.pptx")
)

print("Saved successfully!")
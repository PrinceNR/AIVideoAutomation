from pathlib import Path

from presentation.template_loader import TemplateLoader
from presentation.slide_duplicator import SlideDuplicator

loader = TemplateLoader()

presentation = loader.load(
    Path("templates/vocabulary_template_v2.pptx")
)

duplicator = SlideDuplicator()

duplicator.duplicate_word_template(
    presentation
)

presentation.save(
    "output/test_duplicate_word_template.pptx"
)

print("Word template duplicated successfully!")

# duplicator.duplicate_slide(
#     presentation,
#     0
# )

# presentation.save(
#     "output/test_duplicate.pptx"
# )

# print("Slide duplicated successfully!")
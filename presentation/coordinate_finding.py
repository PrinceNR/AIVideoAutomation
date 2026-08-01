# from pathlib import Path
# from pptx import Presentation
# from pptx.enum.shapes import MSO_SHAPE_TYPE

# presentation = Presentation(
#     Path("templates/vocabulary_template_v2.pptx")
# )

# for slide_no, slide in enumerate(presentation.slides, start=1):
#     print(f"\nSlide {slide_no}")

#     for i, shape in enumerate(slide.shapes, start=1):
#         print(
#             i,
#             shape.name,
#             shape.shape_type
#         )

from pathlib import Path
from pptx import Presentation

prs = Presentation("templates/vocabulary_template_v2.pptx")

for i, slide in enumerate(prs.slides, start=1):

    print(f"\nSlide {i}")

    for shape in slide.shapes:

        print(
            shape.name,
            shape.shape_type,
            shape.left,
            shape.top,
            shape.width,
            shape.height
        )
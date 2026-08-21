from pathlib import Path
from presentation.image_compatibility import (
    PresentationImageCompatibility,
)
from presentation.visual_slot_locator import (
    VisualSlotLocator
)


class ImageProcessor:

    def __init__(self):
        self.locator = VisualSlotLocator()
        self.image_compatibility = PresentationImageCompatibility()

    def process(
        self,
        slide,
        slide_definition,
        word,
        word_number,
        total_words,
        timeline
    ):
        if not word.default_image:
            return

        picture = self.locator.find_picture(
            slide
        )

        if picture is None:
            return

        left = picture.left
        top = picture.top
        width = picture.width
        height = picture.height

        original_name = picture.name

        image_path = self.image_compatibility.prepare(
            Path(word.default_image)
        )

        picture._element.getparent().remove(
            picture._element
        )

        new_picture = slide.shapes.add_picture(
            str(image_path),
            left,
            top,
            width,
            height
        )

        new_picture.name = original_name

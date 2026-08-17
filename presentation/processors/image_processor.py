from pathlib import Path
from presentation.visual_slot_locator import (
    VisualSlotLocator
)


class ImageProcessor:

    def __init__(self):
        self.locator = VisualSlotLocator()

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

        picture._element.getparent().remove(
            picture._element
        )

        slide.shapes.add_picture(
            str(Path(word.default_image)),
            left,
            top,
            width,
            height
        )
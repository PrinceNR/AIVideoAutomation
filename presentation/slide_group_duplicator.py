from presentation.slide_duplicator import SlideDuplicator


class SlideGroupDuplicator:

    def __init__(self):

        self.slide_duplicator = SlideDuplicator()

    def duplicate_group(
        self,
        presentation,
        start_slide: int,
        slide_count: int
    ):

        new_slides = []

        for index in range(start_slide, start_slide + slide_count):

            slide = self.slide_duplicator.duplicate_slide(
                presentation,
                index
            )

            new_slides.append(slide)

        return new_slides
from copy import deepcopy
from pptx.enum.shapes import MSO_SHAPE_TYPE
from presentation.group_copier import GroupCopier


class SlideDuplicator:


    def __init__(self):

        self.group_copier = GroupCopier()

    def duplicate_slide(
        self,
        presentation,
        slide_index
    ):

        source_slide = presentation.slides[slide_index]

        new_slide = presentation.slides.add_slide(
            source_slide.slide_layout
        )

        self.group_copier.copy_shapes(
            source_slide,
            new_slide
        )

        return new_slide

    # def duplicate_slide(
    #     self,
    #     presentation,
    #     slide_index: int
    # ):

    #     source_slide = presentation.slides[slide_index]

    #     # Create a blank slide with the same layout
    #     new_slide = presentation.slides.add_slide(
    #         source_slide.slide_layout
    #     )

    #     # Copy every shape
    #     for shape in source_slide.shapes:

    #         new_element = deepcopy(shape.element)

    #         new_slide.shapes._spTree.insert_element_before(
    #             new_element,
    #             "p:extLst"
    #         )

    #     return new_slide

    # def duplicate_word_template(
    #     self,
    #     presentation,
    #     start_slide: int = 0,
    #     slide_count: int = 4
    # ):

    #     new_slides = []

    #     for index in range(slide_count):

    #         slide = self.duplicate_slide(
    #             presentation,
    #             start_slide + index
    #         )

    #         new_slides.append(slide)

    #     return new_slides
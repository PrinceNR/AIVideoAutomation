from copy import deepcopy


class ShapeCopier:

    def copy(
        self,
        source_shape,
        destination_slide
    ):

        new_element = deepcopy(
            source_shape.element
        )

        destination_slide.shapes._spTree.insert_element_before(
            new_element,
            "p:extLst"
        )
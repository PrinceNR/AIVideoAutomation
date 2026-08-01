from pptx.enum.shapes import MSO_SHAPE_TYPE

from presentation.shape_copier import ShapeCopier
from presentation.picture_copier import PictureCopier


class GroupCopier:

    def __init__(self):

        self.shape_copier = ShapeCopier()
        self.picture_copier = PictureCopier()

    def copy_shapes(
        self,
        source_slide,
        destination_slide
    ):

        for shape in source_slide.shapes:

            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:

                self.picture_copier.copy(
                    shape,
                    destination_slide
                )

            else:

                self.shape_copier.copy(
                    shape,
                    destination_slide
                )
from io import BytesIO


class PictureCopier:

    def copy(
        self,
        source_shape,
        destination_slide
    ):

        image = source_shape.image

        image_stream = BytesIO(image.blob)

        destination_slide.shapes.add_picture(
            image_stream,
            source_shape.left,
            source_shape.top,
            source_shape.width,
            source_shape.height
        )
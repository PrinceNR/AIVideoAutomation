class ComVisualSlotLocator:

    EMU_PER_POINT = 12700

    IMAGE_LEFT_EMU = 1223367
    IMAGE_TOP_EMU = 728662
    IMAGE_WIDTH_EMU = 3344465

    TOLERANCE = 2.0

    def __init__(self):

        self.expected_left = (
            self.IMAGE_LEFT_EMU
            / self.EMU_PER_POINT
        )

        self.expected_top = (
            self.IMAGE_TOP_EMU
            / self.EMU_PER_POINT
        )

        self.expected_width = (
            self.IMAGE_WIDTH_EMU
            / self.EMU_PER_POINT
        )

    def find_picture(
        self,
        slide
    ):

        for index in range(
            1,
            slide.Shapes.Count + 1
        ):

            shape = slide.Shapes(
                index
            )

            if self._matches(
                shape
            ):
                return shape

        return None

    def _matches(
        self,
        shape
    ):

        try:

            return (
                abs(
                    shape.Left
                    - self.expected_left
                )
                <= self.TOLERANCE

                and abs(
                    shape.Top
                    - self.expected_top
                )
                <= self.TOLERANCE

                and abs(
                    shape.Width
                    - self.expected_width
                )
                <= self.TOLERANCE
            )

        except Exception:

            return False
class SlideTimingController:

    def set_slide_duration(
        self,
        slide,
        duration: float
    ):
        """
        Set the automatic advance time for a PowerPoint slide.
        """

        if duration <= 0:
            raise ValueError(
                "Slide duration must be greater than 0."
            )

        slide.SlideShowTransition.AdvanceOnTime = True
        slide.SlideShowTransition.AdvanceTime = duration

        print(
            f"  Slide timing set: {duration:.2f}s"
        )
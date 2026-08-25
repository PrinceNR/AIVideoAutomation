class SlideEndTimeCalculator:
    """Calculates slide end time from teaching timeline requirements."""

    @staticmethod
    def calculate(
        latest_audio_end=0.0,
        latest_handwriting_end=0.0,
        latest_visual_end=0.0,
        end_padding=0.0,
    ):
        values = {
            "latest_audio_end": float(latest_audio_end),
            "latest_handwriting_end": float(
                latest_handwriting_end
            ),
            "latest_visual_end": float(latest_visual_end),
            "end_padding": float(end_padding),
        }

        if any(value < 0 for value in values.values()):
            raise ValueError(
                "Slide timing requirements cannot be negative."
            )

        required_end = max(
            values["latest_audio_end"],
            values["latest_handwriting_end"],
            values["latest_visual_end"],
        )
        return required_end + values["end_padding"]

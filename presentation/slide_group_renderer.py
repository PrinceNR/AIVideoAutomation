from presentation.slide_renderer import SlideRenderer


class SlideGroupRenderer:

    def __init__(self):

        self.slide_renderer = SlideRenderer()

    def render(
        self,
        slides,
        slide_definitions,
        word,
        word_number,
        total_words
    ):

        for slide, definition in zip(
            slides,
            slide_definitions
        ):

            self.slide_renderer.render(
                slide,
                definition,
                word,
                word_number,
                total_words
            )
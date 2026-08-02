from presentation.slide_renderer import SlideRenderer


class SlideGroupRenderer:

    def __init__(self):

        self.slide_renderer = SlideRenderer()

    def render(
        self,
        slides,
        word,
        word_number,
        total_words
    ):

        for slide in slides:

            self.slide_renderer.render(
                slide,
                word,
                word_number,
                total_words
            )
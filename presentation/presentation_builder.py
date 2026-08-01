from presentation.template_loader import TemplateLoader
from presentation.slide_duplicator import SlideDuplicator
from presentation.slide_renderer import SlideRenderer


class PresentationBuilder:

    def __init__(self):

        self.loader = TemplateLoader()
        self.duplicator = SlideDuplicator()
        self.renderer = SlideRenderer()
       

    def build(
        self,
        lesson,
        template_path,
        output_path
    ):
        # print("here is your lesson :-"lesson)
        presentation = self.loader.load(
        template_path
        )

        template_slide = presentation.slides[0]

        for index, word in enumerate(lesson.words, start=1):

            if index == 1:
                slide = template_slide
            else:
                slide = self.duplicator.duplicate_slide(
                    presentation,
                    0
                )

            print(f"Rendering slide #{index}")
            print("Builder slide:", id(slide))

            self.renderer.render(
                slide,
                word,
                index,
                len(lesson.words)
            )

        presentation.save(
            output_path
        )

        print("Presentation created successfully!")
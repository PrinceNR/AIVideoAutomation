from presentation.template_loader import TemplateLoader
from presentation.slide_group_renderer import SlideGroupRenderer
from presentation.slide_group_duplicator import SlideGroupDuplicator
from presentation.slide_group_manager import SlideGroupManager


class PresentationBuilder:

    def __init__(self):

        self.loader = TemplateLoader()
        self.duplicator = SlideGroupDuplicator()
        self.renderer = SlideGroupRenderer() 
        self.manager = SlideGroupManager()    

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

        # template_group = [presentation.slides[i] for i in range(4)]

        # template_slide = presentation.slides[0]

        # Duplicate remaining groups
        for _ in range(len(lesson.words) - 1):

            self.duplicator.duplicate_group(
                presentation,
                0,
                4
            )

        # Render every word
        for index, word in enumerate(lesson.words):

            slides = self.manager.get_group(
                presentation,
                index
            )

            self.renderer.render(
                slides,
                word,
                index + 1,
                len(lesson.words)
            )

        presentation.save(output_path)

        print("Presentation created successfully!")

        # for index, word in enumerate(lesson.words, start=1):

        #     if index == 1:
        #         slides = template_group
        #     else:
        #         slides = self.duplicator.duplicate_group(
        #             presentation,
        #             0,
        #             4
        #         )

        #     print(f"Rendering word {index}")


        #     self.renderer.render(
        #         slides,
        #         word,
        #         index,
        #         len(lesson.words)
        #     )

        # presentation.save(
        #     output_path
        # )

        
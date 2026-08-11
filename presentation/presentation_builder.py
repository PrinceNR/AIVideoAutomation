from presentation.template_loader import TemplateLoader
from presentation.slide_group_renderer import SlideGroupRenderer
from presentation.slide_group_duplicator import SlideGroupDuplicator
from presentation.slide_group_manager import SlideGroupManager
from presentation.template_definition_loader import TemplateDefinitionLoader
from presentation.postprocessor.pptx_post_processor import PptxPostProcessor
from presentation.audio_presentation_processor import (AudioPresentationProcessor)


class PresentationBuilder:

    def __init__(self):

        self.loader = TemplateLoader()
        self.duplicator = SlideGroupDuplicator()
        self.renderer = SlideGroupRenderer() 
        self.manager = SlideGroupManager()   
        self.template_loader = TemplateDefinitionLoader()
        self.post_processor = PptxPostProcessor() 
        self.audio_presentation_processor = AudioPresentationProcessor()

    def build(
        self,
        lesson,
        template_path,
        output_path
    ):
        presentation = self.loader.load(
        template_path
        )

        template_definition = self.template_loader.load(
        "templates/vocabulary/template_definition.json"
        )
        print(
            "Slides per word:",
            template_definition.slides_per_word
        )
    
        # Duplicate remaining groups
        for _ in range(len(lesson.words) - 1):

            self.duplicator.duplicate_group(
                presentation,
                0,
                template_definition.slides_per_word
            )

        # Render every word
        for index, word in enumerate(lesson.words):

            slides = self.manager.get_group(
                presentation,
                index
            )

            self.renderer.render(
                slides,
                template_definition.slides,
                word,               
                index + 1,
                len(lesson.words)
            )

            # timelines = self.renderer.render(
            #     slides,
            #     template_definition.slides,
            #     word,
            #     index + 1,
            #     len(lesson.words)
            # )

        presentation.save(output_path)

        self.post_processor.process(
            output_path
        )

        print("Base presentation created.")

        # -------------------------------------------------
        # Embed audio and apply slide timings
        # -------------------------------------------------

        template_definition = self.template_loader.load(
            "templates/vocabulary/template_definition.json"
        )

        self.audio_presentation_processor.process(
            pptx_path=output_path,
            lesson=lesson,
            template_definition=template_definition
        )

        print("Presentation created successfully!")


        
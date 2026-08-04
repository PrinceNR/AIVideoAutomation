from presentation.template_loader import TemplateLoader
from presentation.slide_group_renderer import SlideGroupRenderer
from presentation.slide_group_duplicator import SlideGroupDuplicator
from presentation.slide_group_manager import SlideGroupManager
from presentation.template_definition_loader import TemplateDefinitionLoader


class PresentationBuilder:

    def __init__(self):

        self.loader = TemplateLoader()
        self.duplicator = SlideGroupDuplicator()
        self.renderer = SlideGroupRenderer() 
        self.manager = SlideGroupManager()   
        self.template_loader = TemplateDefinitionLoader() 

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

        presentation.save(output_path)

        print("Presentation created successfully!")


        
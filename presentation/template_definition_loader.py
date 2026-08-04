import json

from presentation.template_definition import (
    TemplateDefinition,
    SlideDefinition,
)


class TemplateDefinitionLoader:

    def load(self, path):

        with open(path, "r", encoding="utf-8") as file:

            data = json.load(file)

        slides = []

        for slide in data["slides"]:

            slides.append(

                SlideDefinition(

                    type=slide["type"],

                    processors=slide["processors"],

                    image=slide.get("image"),

                    audio_sequence=slide.get("audio_sequence", [])

                )

            )

        return TemplateDefinition(

            template_name=data["template_name"],

            slides_per_word=data["slides_per_word"],

            slides=slides

        )
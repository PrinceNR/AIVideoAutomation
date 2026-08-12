import json

from presentation.template_definition import (
    TemplateDefinition,
    SlideDefinition,
    AudioConfiguration,
)
from config import (
    AUDIO_INITIAL_DELAY,
    AUDIO_GAP,
)


class TemplateDefinitionLoader:

    def load(self, path):

        with open(path, "r", encoding="utf-8") as file:

            data = json.load(file)

        slides = []

        for slide in data["slides"]:

            audio_config = None

            if "audio" in slide:

                audio_data = slide["audio"]

                audio_config = AudioConfiguration(
                    sequence=audio_data.get(
                        "sequence",
                        []
                    ),

                    initial_delay=audio_data.get(
                        "initial_delay",
                        AUDIO_INITIAL_DELAY
                    ),

                    gap=audio_data.get(
                        "gap",
                        AUDIO_GAP
                    )
                )

            slides.append(

                SlideDefinition(

                    type=slide["type"],

                    processors=slide["processors"],

                    image=slide.get("image"),

                    audio=audio_config
                )
            )

        return TemplateDefinition(

            template_name=data["template_name"],

            slides_per_word=data["slides_per_word"],

            slides=slides

        )
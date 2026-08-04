from dataclasses import dataclass


@dataclass
class SlideDefinition:

    type: str

    processors: list[str]

    image: str | None = None

    audio_sequence: list[str] | None = None


@dataclass
class TemplateDefinition:

    template_name: str

    slides_per_word: int

    slides: list[SlideDefinition]
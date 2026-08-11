from dataclasses import dataclass


@dataclass
class AudioConfiguration:

    sequence: list[str]

    initial_delay: float = 0.5

    gap: float = 0.3


@dataclass
class SlideDefinition:

    type: str

    processors: list[str]

    image: str | None = None

    audio: AudioConfiguration | None = None


@dataclass
class TemplateDefinition:

    template_name: str

    slides_per_word: int

    slides: list[SlideDefinition]
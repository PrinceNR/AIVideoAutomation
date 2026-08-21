from dataclasses import dataclass, field

from models.word import Word


@dataclass
class Lesson:

    title: str

    topic: str
    suggestions: str = ""

    words: list[Word] = field(default_factory=list)

    content_verification: dict = field(
        default_factory=dict
    )

    stage1_readiness: dict = field(
        default_factory=dict
    )

import json
from pathlib import Path

from ai.content_generator import (
    build_vocabulary_prompt
)

from utils.file_manager import FileManager
from models.lesson_mapper import LessonMapper

from verification.semantic_lesson_verifier import (
    SemanticLessonVerifier
)


def main():

    lesson_path = Path(
        "output/medium_action_vocabulary/lesson.json"
    )

    file_manager = FileManager()

    lesson = file_manager.load_lesson(
        lesson_path
    )

    lesson_dict = LessonMapper.to_dict(
        lesson
    )

    generation_prompt = (
        build_vocabulary_prompt(
            topic=lesson.topic,
            count=len(lesson.words),
            suggestions=lesson.suggestions
        )
    )

    verifier = SemanticLessonVerifier()

    report = verifier.verify(
        lesson_dict,
        generation_prompt=generation_prompt
    )

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
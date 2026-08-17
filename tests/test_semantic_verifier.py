import copy
import json

from utils.file_manager import FileManager
from models.lesson_mapper import LessonMapper
from verification.semantic_lesson_verifier import (
    SemanticLessonVerifier
)


def main():

    lesson_path = (
        "output/action_vocabulary/lesson.json"
    )

    file_manager = FileManager()

    lesson = file_manager.load_lesson(
        lesson_path
    )

    lesson_dict = LessonMapper.to_dict(
        lesson
    )

    # Work on a copy.
    # Never modify the real lesson.
    test_lesson = copy.deepcopy(
        lesson_dict
    )

    words = test_lesson["words"]

    # -----------------------------------
    # INTENTIONAL ERRORS
    # -----------------------------------

    # 1. Wrong meaning
    words[0]["meaning"] = (
        "To sleep quietly during the night."
    )

    # 2. Transliteration instead of translation
    words[1]["translations"]["malayalam"] = (
        "ക്ലാപ്"
    )

    # 3. Completely wrong synonym
    words[2]["synonyms"].append(
        "eat"
    )

    # 4. Wrong verb form
    words[3]["past_form"] = (
        "catched"
    )

    # 5. Wrong tense / usage
    words[4]["future_sentence"] = (
        "The child waved goodbye yesterday."
    )

    # 6. Completely unrelated image query
    words[4]["search_query"] = (
        "red sports car parked on road"
    )

    print(
        "Running semantic verifier "
        "with intentional errors...\n"
    )

    verifier = SemanticLessonVerifier()

    report = verifier.verify(
        test_lesson
    )

    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
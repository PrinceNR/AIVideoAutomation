import json
from pathlib import Path

from utils.file_manager import FileManager

from image_engine.image_verifier import (
    ImageVerifier
)


def main():

    lesson_path = Path(
        "output/words_starts_with_k/lesson.json"
    )

    file_manager = FileManager()

    lesson = file_manager.load_lesson(
        lesson_path
    )

    # Test "knock"
    target_word = None

    for word in lesson.words:

        if word.word.lower() == "knock":

            target_word = word
            break

    if target_word is None:

        raise ValueError(
            "Word 'knock' not found."
        )

    image_folder = Path(
        target_word.image_folder
    )

    image_paths = sorted(
        [
            path
            for path in image_folder.iterdir()
            if path.suffix.lower()
            in {
                ".jpg",
                ".jpeg",
                ".png"
            }
        ]
    )

    print(
        f"\nTesting image verification "
        f"for: {target_word.word}"
    )

    print(
        f"Meaning: "
        f"{target_word.meaning}"
    )

    print(
        f"Search query: "
        f"{target_word.search_query}"
    )

    print(
        f"Candidate images: "
        f"{len(image_paths)}\n"
    )

    verifier = ImageVerifier()

    result = verifier.verify(
        target_word,
        image_paths
    )

    print(
        "\nIMAGE VERIFICATION RESULT\n"
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
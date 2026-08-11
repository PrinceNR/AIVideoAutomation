from pathlib import Path
from utils.file_manager import FileManager
from presentation.presentation_builder import PresentationBuilder
# from presentation.audio_presentation_processor import (
#     AudioPresentationProcessor
# )
# from presentation.template_definition_loader import (
#     TemplateDefinitionLoader
# )

# Import however your project currently loads Lesson.
# If your existing test already has a Lesson object,
# copy that loading code here.


def main():

    template_path = Path(
        "templates/vocabulary_template_v2.pptx"
    )

    output_path = Path(
        "research/audio_full_test.pptx"
    )
    file_manager = FileManager()

    # --------------------------------------------------
    # IMPORTANT:
    # Use the SAME lesson-loading code that you already
    # use in tests/test_presentation_builder.py
    # --------------------------------------------------
    builder = PresentationBuilder()

    lesson = file_manager.load_lesson(
        Path("output/farming/lesson.json")
    )  # <-- existing lesson-loading code


    builder.build(
        lesson=lesson,
        template_path=template_path,
        output_path=output_path
    )

    print("\nFinal presentation:")
    print(output_path)

    # print("\nBase presentation created.")

    # template_definition_loader = (
    #     TemplateDefinitionLoader()
    # )

    # template_definition = (
    #     template_definition_loader.load(
    #         "templates/vocabulary/template_definition.json"
    #     )
    # )

    # audio_processor = AudioPresentationProcessor()

    # audio_processor.process(
    #     pptx_path=output_path,
    #     lesson=lesson,
    #     template_definition=template_definition
    # )

    # print("\nFinal audio presentation:")
    # print(output_path)


if __name__ == "__main__":
    main()
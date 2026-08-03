from pathlib import Path

from presentation.presentation_builder import PresentationBuilder
from utils.file_manager import FileManager

file_manager = FileManager()

lesson = file_manager.load_lesson(
    Path("output/farming/lesson.json")
)

builder = PresentationBuilder()

builder.build(
    lesson=lesson,
    template_path=Path("templates/vocabulary_template_v2.pptx"),
    output_path=Path("output/test_builder.pptx")
)
from pathlib import Path
import json
import re
from models.lesson import Lesson
from models.lesson_mapper import LessonMapper
from config import OUTPUT_FOLDER

class FileManager:

    def __init__(self):
        self.output_folder = Path(OUTPUT_FOLDER)
        self.output_folder.mkdir(exist_ok=True)

    def make_folder_name(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[\\/:*?"<>|]', '', text)
        text = re.sub(r'[^a-z0-9\s_-]', '', text)
        text = re.sub(r'\s+', '_', text)
        text = re.sub(r'_+', '_', text)
        text = text.strip("_")
        return text

    def create_lesson_folder(self, topic: str) -> Path:

        folder = self.output_folder / self.make_folder_name(topic)

        folder.mkdir(exist_ok=True)

        return folder

    def save_json(self, data: dict, file_path: Path):

        with open(file_path, "w", encoding="utf-8") as file:

            json.dump(data, file, indent=4, ensure_ascii=False)

    def load_json(self, file_path: Path):

        with open(file_path, "r", encoding="utf-8") as file:

            return json.load(file)

    def load_lesson(self, path: Path) -> Lesson:

        data = self.load_json(path)

        return LessonMapper.from_dict(data)
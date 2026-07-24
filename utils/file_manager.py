from pathlib import Path
import json


class FileManager:
    def __init__(self):
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def create_lesson_folder(self, topic: str) -> Path:
        folder_name = topic.lower().replace(" ", "_")
        lesson_path = self.output_dir / folder_name
        lesson_path.mkdir(exist_ok=True)
        return lesson_path

    def save_json(self, data: dict, file_path: Path):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load_json(self, file_path: Path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
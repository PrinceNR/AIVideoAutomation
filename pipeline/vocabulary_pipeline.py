from ai.content_generator import generate_vocabulary
from image_engine.image_downloader import ImageDownloader
from utils.file_manager import FileManager
from audio_engine.audio_generator import AudioGenerator
from models.lesson_mapper import LessonMapper


class VocabularyPipeline:

    def __init__(self):

        self.file_manager = FileManager()
        self.image_downloader = ImageDownloader()
        self.audio_generator = AudioGenerator()

    def run(self, topic: str, count: int):

        print("Generating lesson...")

        lesson = generate_vocabulary(topic, count)

        lesson_folder = self.file_manager.create_lesson_folder(topic)

        lesson_path = lesson_folder / "lesson.json"

        lesson_dict = LessonMapper.to_dict(lesson)

        self.file_manager.save_json(
            lesson_dict,
            lesson_path
        )

        print("Downloading images...")


        lesson = self.file_manager.load_lesson(lesson_path)

        for word in lesson.words:

            self.image_downloader.download_word_images(
                word,
                lesson_folder
            )

            self.audio_generator.generate_word_audio(
                word,
                lesson_folder
            )

        lesson_dict = LessonMapper.to_dict(lesson)

        self.file_manager.save_json(
            lesson_dict,
            lesson_path
        ) 
        

        print("\nPipeline completed successfully!")

        return lesson_path

if __name__ == "__main__":

    pipeline = VocabularyPipeline()

    topic = input("Enter topic: ").strip()

    count = int(
        input("Enter number of words: ")
    )

    pipeline.run(
        topic=topic,
        count=count
    )
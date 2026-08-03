from pathlib import Path
from presentation.processors.image_processor import ImageProcessor
from presentation.processors.text_processor import TextProcessor


class SlideRenderer:

    def __init__(self):

        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()

    def render(
        self,
        slide,
        word,
        word_number,
        total_words
    ):  

        print(f"Rendering word: {word.word}")
        print("Slide object:", id(slide))
        self.text_processor.replace_word(
            slide,
            word,
            word_number,
            total_words
        )
        print("default_image:", word.default_image)
        print("image_folder:", word.image_folder)
        print("default_audio:", word.default_audio)

        self.image_processor.replace_image(
            slide,
          
            Path(word.default_image)
        )
        

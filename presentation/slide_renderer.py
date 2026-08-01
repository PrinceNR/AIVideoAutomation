from pathlib import Path
from presentation.placeholder_replacer import PlaceholderReplacer
from presentation.image_replacer import ImageReplacer

class SlideRenderer:

    def __init__(self):

        self.text_replacer = PlaceholderReplacer()
        self.image_replacer = ImageReplacer()

    def render(
        self,
        slide,
        word,
        word_number,
        total_words
    ):  

        print(f"Rendering word: {word.word}")
        print("Slide object:", id(slide))
        self.text_replacer.replace_word(
            slide,
            word,
            word_number,
            total_words
        )
        print("default_image:", word.default_image)
        print("image_folder:", word.image_folder)
        print("default_audio:", word.default_audio)

        self.image_replacer.replace_image(
            slide,
          
            Path(word.default_image)
        )
        

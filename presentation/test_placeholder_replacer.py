from pathlib import Path

from presentation.template_loader import TemplateLoader
from presentation.placeholder_replacer import PlaceholderReplacer
from models.word import Word

word = Word(
    word="Algorithm",
    meaning="A step-by-step procedure used to solve a problem.",
    pronunciation="/ˈælɡəˌrɪðəm/",
    part_of_speech="Noun",
    difficulty="Beginner",

    translations={
        "malayalam": "അൽഗോരിതം",
        "tamil": "அல்காரிதம்",
        "hindi": "एल्गोरिदम",
    },

    present_sentence="I use an algorithm to solve the problem.",
    past_sentence="Yesterday I learned an algorithm.",
    future_sentence="Tomorrow I will study a new algorithm.",

    base_form="",
    present_form="",
    past_form="",

    synonyms=["procedure", "method"],
    antonyms=[],

    image_keywords=["algorithm", "coding"],
    search_query="computer algorithm illustration",

    image_folder=None,
    audio_folder=None
)


loader = TemplateLoader()
presentation = loader.load(
    Path("templates/vocabulary_template_v2.pptx")
)

replacer = PlaceholderReplacer()

replacer.replace_text(
    presentation,
    "{{WORD}}",
    "Algorithm"
)

replacer.replace_word(
    presentation,
    word,
    word_number=1,
    total_words=20
)

presentation.save(
    "output/test_placeholder.pptx"
)

print("Placeholder replaced successfully!")


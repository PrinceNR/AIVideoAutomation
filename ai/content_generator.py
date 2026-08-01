import json

from ai.gemini_client import client
from models.lesson_mapper import LessonMapper
from ai.prompts import VOCABULARY_PROMPT


def generate_vocabulary(topic, count):

    prompt = VOCABULARY_PROMPT.format(
        topic=topic,
        count=count
    )

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )
    text = response.text.strip()

    data = json.loads(text)

    lesson = LessonMapper.from_dict(data)

    return lesson

    # text = response.text.strip()

    # return json.loads(text)
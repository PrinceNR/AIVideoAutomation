VOCABULARY_PROMPT = """
Generate {count} English vocabulary lessons related to "{topic}".

Return ONLY valid JSON.

The JSON format should be:

{{
    "title": "{topic} Vocabulary",
    "topic": "{topic}",
    "words": [
        {{
            "word": "",
            "meaning": "",
            "pronunciation": "",
            "part_of_speech": "",
            "difficulty": "",

            "translations": {{
                "malayalam": "",
                "tamil": "",
                "hindi": ""
            }},

            "present_sentence": "",
            "past_sentence": "",
            "future_sentence": "",

            "base_form": "",
            "present_form": "",
            "past_form": "",

            "synonyms": [],
            "antonyms": [],

            "image_keywords": [],

            "search_query": ""
        }}
    ]
}}

Rules:

1. Return ONLY valid JSON.
2. Do NOT use markdown.
3. Do NOT use ```json.
4. Generate exactly {count} words.
5. Use simple English suitable for vocabulary learners.
6. The present, past and future sentences should all use the vocabulary word naturally.
7. Keep meanings short (one sentence).
8. Generate 2-5 image keywords for each word.
9. The search_query should describe the best image to search for that meaning.
10. Synonyms and antonyms may contain 2-5 words each.
11. If the word is a noun or adjective and verb forms are not applicable, keep:
    "base_form": "",
    "present_form": "",
    "past_form": ""
12. Translate only the meaning of the word into Malayalam, Tamil and Hindi.
"""
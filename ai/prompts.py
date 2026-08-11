
VOCABULARY_PROMPT = """
Generate {count} English vocabulary words related to "{topic}".

Return ONLY valid JSON.
Do not use markdown.
Do not wrap the response in ```json.

JSON format:

{{
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

            "image_keywords": []
        }}
    ]
}}

Rules:

1. Return ONLY JSON.

2. "word" must contain only the English vocabulary word.

3. "meaning" must be ONE short English dictionary definition.
   Maximum 15 words.

4. "translations" must contain ONLY the translated WORD.
   Do NOT translate the English definition.

   Example:

   Word:
   Campus

   Malayalam:
   കാമ്പസ്

   NOT

   കോളേജിന്റെയോ സർവകലാശാലയുടെയോ ഭൂമിയും...

5. Generate ONE Present tense sentence.

6. Generate ONE Past tense sentence.

7. Generate ONE Future tense sentence.

8. Sentences should:
   - be natural
   - easy to understand
   - between 8 and 15 words
   - clearly use the vocabulary word

9. If the word is NOT a verb,
   leave

   base_form
   present_form
   past_form

   as empty strings.

10. If the word IS a verb,
    fill

    base_form
    present_form
    past_form

    correctly.

11. Generate 3-5 useful image search keywords.

Example:

[
    "campus",
    "college",
    "university",
    "students",
    "education"
]

12. Generate 3-5 common synonyms.

13. Generate 2-5 common antonyms whenever possible.

14. Difficulty must be one of:

Beginner
Intermediate
Advanced

15. Pronunciation must be IPA.

Example:

/ˈkæm.pəs/
"""
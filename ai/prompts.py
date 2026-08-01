# VOCABULARY_PROMPT = """
# Generate {count} English vocabulary lessons related to "{topic}".

# Return ONLY valid JSON.

# The JSON format should be:

# {{
#     "title": "{topic} Vocabulary",
#     "topic": "{topic}",
#     "words": [
#         {{
#             "word": "",
#             "meaning": "",
#             "pronunciation": "",
#             "part_of_speech": "",
#             "difficulty": "",

#             "translations": {{
#                 "malayalam": "",
#                 "tamil": "",
#                 "hindi": ""
#             }},

#             "present_sentence": "",
#             "past_sentence": "",
#             "future_sentence": "",

#             "base_form": "",
#             "present_form": "",
#             "past_form": "",

#             "synonyms": [],
#             "antonyms": [],

#             "image_keywords": [],

#             "search_query": ""
#         }}
#     ]
# }}

# Rules:

# 1. Return ONLY valid JSON.
# 2. Do NOT use markdown.
# 3. Do NOT use ```json.
# 4. Generate exactly {count} words.
# 5. Use simple English suitable for vocabulary learners.
# 6. The present, past and future sentences should all use the vocabulary word naturally.
# 7. Keep meanings short (one sentence).
# 8. Generate 2-5 image keywords for each word.
# 9. The search_query should describe the best image to search for that meaning.
# 10. Synonyms and antonyms may contain 2-5 words each.
# 11. If the word is a noun or adjective and verb forms are not applicable, keep:
#     "base_form": "",
#     "present_form": "",
#     "past_form": ""
# 12. Translate only the meaning of the word into Malayalam, Tamil and Hindi.
# """
# version 2 prompt 

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
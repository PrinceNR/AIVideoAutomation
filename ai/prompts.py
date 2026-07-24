VOCABULARY_PROMPT = """
Generate {count} English vocabulary words related to "{topic}".

Return ONLY valid JSON.

The JSON format should be:

{{
    "topic": "{topic}",
    "words": [
        {{
            "word": "",
            "meaning": "",
            "part_of_speech": "",
            "difficulty": "",
            "pronunciation": "",
            "translations": {{
                "malayalam": "",
                "tamil": "",
                "hindi": ""
            }},
            "sentences": [
                "",
                "",
                ""
            ]
        }}
    ]
}}

Rules:
1. Return only JSON.
2. Do not add markdown.
3. Do not use ```json.
4. Every word must contain exactly 3 sentences.
"""
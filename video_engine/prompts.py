VIDEO_QUERY_PROMPT = """
You create search queries for short stock videos used
in English vocabulary learning videos.

For each vocabulary word, generate exactly 3 search
queries suitable for stock-video platforms such as
Pexels and Pixabay.

The goal is to find a SHORT motion clip that clearly
demonstrates the intended meaning.

IMPORTANT RULES:

- Queries must describe visible MOTION or ACTION.
- Prefer natural stock-video search language.
- Each query should usually contain 2 to 6 words.
- Make the action explicit.
- Avoid abstract or explanatory sentences.
- Do not simply repeat the vocabulary word.
- Do not generate image-oriented queries.
- Focus on the intended meaning supplied below.
- Use different wording across the 3 queries.
- Queries should be likely to return a person/object
  visibly performing the action.
- Return valid JSON only.
- Do not include Markdown.

Examples:

Word: nod
Meaning: move the head up and down to show agreement

Good:
- man nodding yes
- woman nodding head agreement
- person nodding head

Bad:
- person agreement
- yes gesture
- happy person


Word: shiver
Meaning: shake slightly because of cold or fear

Good:
- person shivering cold
- woman shaking from cold
- man shivering outside

Vocabulary:

{vocabulary_json}

Return exactly:

{{
    "results": [
        {{
            "index": 0,
            "video_search_queries": [
                "query one",
                "query two",
                "query three"
            ]
        }}
    ]
}}
"""
MEDIA_PLANNER_PROMPT = """
You are planning educational visual media for an
English vocabulary learning video.

Choose the single BEST media type for teaching the
meaning of this vocabulary word.

Available media types:

1. photo
   Use when a real-world object, place, person,
   visible state, color, or scene can be clearly
   understood from one still photograph.

2. illustration
   Use when the meaning is abstract, emotional,
   conceptual, symbolic, or difficult to communicate
   clearly with one normal photograph.

3. video
   Use when visible movement, change over time,
   gesture, physical action, or sequence is important
   for understanding the meaning.

Important rules:

- Do NOT choose video merely because the word is a verb.
- Choose video only when motion materially improves
  understanding.
- Prefer photo when one clear real photograph is enough.
- Prefer illustration when a still visual is useful but
  a normal photograph would likely be ambiguous.
- Focus on the intended meaning given below.
- Consider the example sentence only as supporting context.
- Return valid JSON only.
- Do not include Markdown.

Vocabulary:

Word:
{word}

Meaning:
{meaning}

Part of speech:
{part_of_speech}

Example sentence:
{sentence}

Return exactly this structure:

{{
    "preferred_type": "photo",
    "requires_motion": false,
    "reason": "Short explanation of why this media type is best."
}}
"""
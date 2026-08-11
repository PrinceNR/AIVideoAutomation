YOUTUBE_METADATA_PROMPT = """
You are creating YouTube metadata for an English vocabulary learning channel.

Topic:
{topic}

Vocabulary words:
{words}

Create SEO-friendly YouTube metadata for this vocabulary lesson.

Requirements:

1. title
- Clear and attractive.
- Natural English.
- Maximum 100 characters.
- Include the main topic.
- Make it suitable for an English vocabulary learning video.
- Do not use clickbait.

2. description
- Explain what the viewer will learn.
- Mention some of the vocabulary words naturally.
- Suitable for beginner/intermediate English learners.
- Keep it concise and useful.
- Do not include hashtags inside the description.

3. tags
- Return 10 to 15 useful YouTube search tags.
- Include topic-specific vocabulary tags.
- Include general English-learning tags.
- Do not include # symbols.

4. hashtags
- Return 3 to 5 relevant hashtags.
- Each hashtag must begin with #.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "title": "",
    "description": "",
    "tags": [],
    "hashtags": []
}}
"""
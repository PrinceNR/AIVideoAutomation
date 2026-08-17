VOCABULARY_PROMPT = """
Generate exactly {count} useful English vocabulary words related to:

TOPIC:
"{topic}"

USER SUGGESTIONS:
"{suggestions}"

The vocabulary is for English learners.

The user's suggestions are IMPORTANT content requirements.
Follow them when selecting vocabulary, difficulty, audience,
and style of examples.

Examples:

If the user asks for:
- "simple words for kids"
  prefer Beginner vocabulary.

- "medium level words"
  or "intermediate words"
  prefer Intermediate vocabulary.

- "advanced words"
  or "high level words"
  prefer Advanced vocabulary.

Do not ignore an explicitly requested difficulty level unless
the requested topic makes it impossible.

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

            "image_keywords": [],
            "search_query": ""
        }}
    ]
}}

RULES:

1. OUTPUT

Return ONLY valid JSON.

Generate exactly {count} DIFFERENT vocabulary words.

Every word must clearly match the topic:

"{topic}"


2. WORD

"word" must contain only the English vocabulary word
or natural phrasal verb.

Use the normal dictionary/base form whenever appropriate.

TOPIC CONSTRAINT RULE:

Every generated vocabulary word MUST satisfy the literal topic
constraint.

For example:

Topic:
"words starts with X"

Every generated word MUST begin with the letter X.

Never fill the requested count using unrelated words merely because
the topic has few common examples.

If the topic is unusually restrictive, choose the closest useful
vocabulary that still satisfies the topic rather than violating
the topic.


3. MEANING

Give ONE short and correct English definition.

Rules:

- Explain the intended meaning used in this lesson.
- Maximum 12 words.
- Use simple English.
- Do NOT list every possible dictionary meaning.
- Choose one useful meaning and use that SAME meaning consistently
  in translations, sentences, synonyms, antonyms, and images.


4. TRANSLATIONS

Translate the INTENDED MEANING of the vocabulary word into:

- Malayalam
- Tamil
- Hindi

IMPORTANT:

The translation must help a native speaker understand
what the English vocabulary word means.

Use the native writing script ONLY.

Malayalam:
- MUST contain Malayalam script.
- NEVER write Malayalam using English/Latin letters.

Example:

GOOD:
"രക്ഷിക്കുക"

BAD:
"rakshikkuka"


Tamil:
- MUST contain Tamil script.
- NEVER write Tamil using English/Latin letters.

Example:

GOOD:
"பாதுகாக்க"

BAD:
"paathukaappu"


Hindi:
- MUST contain Devanagari script.
- NEVER write Hindi using English/Latin letters.

Example:

GOOD:
"बचाना"

BAD:
"bachana"


Do NOT simply transliterate the English vocabulary word.

Example:

Word:
reluctant

Meaning:
unwilling to do something

Good Malayalam:
"ചെയ്യാൻ മടിയുള്ള"

Bad Malayalam:
"റിലക്ടന്റ്"


The translation should match the intended PART OF SPEECH
whenever a natural equivalent exists.

Example:

English verb:
protect

Prefer a verb meaning "to protect",
not a noun meaning "protection".

Prefer a short, natural translation instead of a long explanation.


5. EXAMPLE SENTENCES

Generate:

- one present-tense sentence
- one past-tense sentence
- one future-tense sentence

Every sentence must:

- clearly demonstrate the intended meaning
- use the target vocabulary naturally
- use simple everyday English
- be easy for English learners
- preferably use one simple clause
- preferably contain about 5 to 12 words
- avoid unnecessary difficult vocabulary
- sound natural when spoken

Do NOT add unnecessary words only to make a sentence longer.

TENSE REQUIREMENTS:

present_sentence:
Must express present tense.

past_sentence:
Must express past tense.

future_sentence:
Must express future tense.


6. VERB FORMS

If the vocabulary word is a verb, correctly fill:

"base_form"
"present_form"
"past_form"

Example:

write
writes
wrote

If the word is NOT a verb:

"base_form": ""
"present_form": ""
"past_form": ""


7. PRONUNCIATION

"pronunciation" must use reasonable IPA.

Use one standard pronunciation.

British or American pronunciation is acceptable.

Example:

/ˈkæm.pəs/


8. PART OF SPEECH

Use the correct part of speech.

Examples:

noun
verb
adjective
adverb
phrasal verb


9. DIFFICULTY

"difficulty" must be exactly one of:

Beginner
Intermediate
Advanced

Respect the user's requested level.

If the user specifically asks for medium-level vocabulary,
prefer Intermediate words.

If the user asks for high-level vocabulary,
prefer Advanced words.

If the user asks for simple/kids vocabulary,
prefer Beginner words.


10. SYNONYMS

Generate 3 to 5 common synonyms when suitable.

Rules:

- They must match the intended meaning.
- Prefer genuine synonyms.
- Avoid words that are merely related to the topic.
- A narrower or broader word is acceptable only when still
  genuinely useful for an English learner.

If there are not enough good synonyms,
return fewer rather than inventing weak ones.


11. ANTONYMS

Generate 2 to 5 common antonyms ONLY when natural antonyms exist.

Do NOT invent opposites just to fill the list.

A different action is NOT automatically an antonym.

If the word has no clear natural antonym:

"antonyms": []


12. IMAGE KEYWORDS

Generate 3 to 5 short image-search phrases.

The phrases should describe visible:

- people
- actions
- objects
- places
- facial expressions
- body language

Avoid abstract words when possible.

Do not only repeat the vocabulary word.

Example for "gossip":

[
    "people whispering",
    "secret conversation",
    "friends talking",
    "whispering friends"
]


13. SEARCH QUERY

"search_query" will be sent directly to stock-image search engines
such as Pexels and Pixabay.

Stock-image search engines work better with short,
literal visual keywords than with long natural-language sentences.

Generate ONE primary stock-search query.

Rules:

- Prefer 2 to 5 words.
- Describe the visible action/object/scene.
- Use common stock-photo vocabulary.
- Avoid abstract concepts.
- Avoid unnecessary words such as:
  "a", "the", "while", "who is"
- Do NOT write a full sentence.
- Do NOT simply repeat the vocabulary word.
- For verbs, make the physical action visible.
- For emotions or abstract words, use visible body language
  or a concrete situation.

Examples:

Word:
run

GOOD:
"child running outdoors"

BAD:
"happy child who is running very fast in the park"


Word:
knock

GOOD:
"person knocking door"


Word:
persuade

GOOD:
"friends serious discussion"

Avoid:
"person convincing friend talking"


Word:
predict

GOOD:
"weather presenter forecast"

Avoid:
"meteorologist pointing at weather map and predicting tomorrow"


Word:
protect

GOOD:
"adult shielding child"


Word:
propose

GOOD:
"man presenting idea"


Word:
reluctant

GOOD:
"hesitant person doorway"


14. VISUAL SUITABILITY

Prefer vocabulary examples and visual scenes that can be
represented clearly using:

- a stock photo
- an illustration
- a cartoon
- or a simple generated scene

However, do NOT reject useful vocabulary merely because it is
slightly abstract.


15. FINAL SELF-CHECK

Before returning JSON, silently check EVERY word.

Confirm:

- word matches "{topic}"
- word follows "{suggestions}"
- difficulty follows the requested audience/level
- meaning is correct
- meaning uses one consistent intended sense
- Malayalam uses Malayalam script
- Tamil uses Tamil script
- Hindi uses Devanagari script
- translations convey the meaning, not pronunciation
- translation part of speech is appropriate
- present sentence uses present tense
- past sentence uses past tense
- future sentence uses future tense
- sentences are simple and natural
- verb forms are correct
- synonyms are genuinely useful
- antonyms are genuine or the list is empty
- image keywords describe visible things
- search_query is short and stock-search friendly

Return ONLY the final JSON.
"""
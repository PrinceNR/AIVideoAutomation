import json

from google.genai import errors

from ai.gemini_client import client

from video_engine.prompts import (
    VIDEO_QUERY_PROMPT
)

from config import (
    GEMINI_CONTENT_MODEL,
    GEMINI_FALLBACK_MODEL
)


class BatchVideoQueryGenerator:

    def generate(
        self,
        words
    ) -> list[list[str]]:

        if not words:
            return []

        prompt = self._build_prompt(
            words
        )

        response = self._generate(
            prompt
        )

        return self._parse(
            response.text,
            expected_count=len(words)
        )

    def _build_prompt(
        self,
        words
    ) -> str:

        vocabulary = []

        for index, word in enumerate(
            words
        ):

            vocabulary.append({
                "index": index,
                "word": word.word,
                "meaning": word.meaning,
                "sentence":
                    word.present_sentence
            })

        vocabulary_json = json.dumps(
            vocabulary,
            ensure_ascii=False,
            indent=2
        )

        return VIDEO_QUERY_PROMPT.format(
            vocabulary_json=(
                vocabulary_json
            )
        )

    def _generate(
        self,
        prompt: str
    ):

        try:

            print(
                "Video query model: "
                f"{GEMINI_CONTENT_MODEL}"
            )

            return (
                client.models.generate_content(
                    model=(
                        GEMINI_CONTENT_MODEL
                    ),
                    contents=prompt
                )
            )

        except errors.ServerError as error:

            if error.code != 503:
                raise

            print(
                f"{GEMINI_CONTENT_MODEL} "
                "is temporarily unavailable."
            )

            print(
                "Trying fallback model: "
                f"{GEMINI_FALLBACK_MODEL}"
            )

            return (
                client.models.generate_content(
                    model=(
                        GEMINI_FALLBACK_MODEL
                    ),
                    contents=prompt
                )
            )

    def _parse(
        self,
        text: str,
        expected_count: int
    ) -> list[list[str]]:

        data = json.loads(
            self._clean_json(
                text
            )
        )

        results = data.get(
            "results",
            []
        )

        if len(results) != expected_count:

            raise ValueError(
                "Unexpected number of "
                "video query results."
            )

        results.sort(
            key=lambda item:
                item["index"]
        )

        query_sets = []

        for expected_index, item in enumerate(
            results
        ):

            if (
                item.get("index")
                != expected_index
            ):

                raise ValueError(
                    "Invalid video query indexes."
                )

            queries = item.get(
                "video_search_queries",
                []
            )

            queries = self._normalize(
                queries
            )

            if len(queries) != 3:

                raise ValueError(
                    "Each video word must have "
                    "exactly 3 search queries."
                )

            query_sets.append(
                queries
            )

        return query_sets

    def _normalize(
        self,
        queries
    ) -> list[str]:

        normalized = []
        seen = set()

        for query in queries:

            if not isinstance(
                query,
                str
            ):
                continue

            clean_query = " ".join(
                query.strip().split()
            )

            if not clean_query:
                continue

            key = clean_query.lower()

            if key in seen:
                continue

            seen.add(key)

            normalized.append(
                clean_query
            )

        return normalized

    def _clean_json(
        self,
        text: str
    ) -> str:

        text = text.strip()

        if text.startswith(
            "```json"
        ):
            text = text[7:]

        elif text.startswith(
            "```"
        ):
            text = text[3:]

        if text.endswith(
            "```"
        ):
            text = text[:-3]

        return text.strip()
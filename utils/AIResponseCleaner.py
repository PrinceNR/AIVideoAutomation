import json


class AIResponseParseError(ValueError):

    def __init__(
        self,
        message,
        *,
        category="invalid",
        diagnostic_snippet="",
    ):
        super().__init__(message)
        self.category = category
        self.diagnostic_snippet = diagnostic_snippet


class AIResponseCleaner:

    DIAGNOSTIC_RADIUS = 120

    @classmethod
    def parse_json_object(
        cls,
        response_text,
        *,
        truncated=False,
    ):

        if not isinstance(response_text, str):
            raise AIResponseParseError(
                "AI response did not contain text."
            )

        text = cls._strip_fence(response_text.strip())

        if not text:
            raise AIResponseParseError(
                "AI response was empty.",
                category=(
                    "incomplete" if truncated else "invalid"
                ),
            )

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as direct_error:
            parsed, extraction_error = (
                cls._extract_first_complete_object(text)
            )

            if parsed is None:
                error = extraction_error or direct_error
                is_incomplete = (
                    truncated
                    or cls._has_unclosed_json(text)
                )
                category = (
                    "incomplete"
                    if is_incomplete
                    else "invalid"
                )
                raise AIResponseParseError(
                    "AI response contained "
                    f"{category} JSON.",
                    category=category,
                    diagnostic_snippet=cls._diagnostic_snippet(
                        text,
                        error.pos,
                    ),
                ) from direct_error

        if not isinstance(parsed, dict):
            raise AIResponseParseError(
                "AI response JSON must be a top-level object."
            )

        return parsed

    @staticmethod
    def _strip_fence(text):

        if not text.startswith("```"):
            return text

        first_newline = text.find("\n")

        if first_newline < 0:
            return text

        text = text[first_newline + 1:]

        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]

        return text.strip()

    @staticmethod
    def _extract_first_complete_object(text):

        decoder = json.JSONDecoder()
        farthest_error = None

        for start, character in enumerate(text):
            if character != "{":
                continue

            try:
                parsed, _end = decoder.raw_decode(text, start)
            except json.JSONDecodeError as error:
                absolute_position = error.pos

                if (
                    farthest_error is None
                    or absolute_position > farthest_error.pos
                ):
                    farthest_error = json.JSONDecodeError(
                        error.msg,
                        text,
                        absolute_position,
                    )

                continue

            if isinstance(parsed, dict):
                return parsed, None

        return None, farthest_error

    @staticmethod
    def _has_unclosed_json(text):

        start = text.find("{")

        if start < 0:
            return False

        stack = []
        in_string = False
        escaped = False

        for character in text[start:]:
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue

            if character == '"':
                in_string = True
            elif character in "[{":
                stack.append(character)
            elif character == "]" and stack:
                if stack[-1] == "[":
                    stack.pop()
            elif character == "}" and stack:
                if stack[-1] == "{":
                    stack.pop()

        return in_string or bool(stack)

    @classmethod
    def _diagnostic_snippet(cls, text, position):

        start = max(0, position - cls.DIAGNOSTIC_RADIUS)
        end = min(
            len(text),
            position + cls.DIAGNOSTIC_RADIUS,
        )
        snippet = text[start:end]
        return snippet.replace("\r", "\\r").replace(
            "\n",
            "\\n",
        )

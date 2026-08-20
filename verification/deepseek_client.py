import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from config import CONTENT_VERIFIER_MODEL


load_dotenv()


class DeepSeekClient:

    MAX_OUTPUT_TOKENS = 16000

    def __init__(self):

        api_key = os.getenv(
            "DEEPSEEK_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not found in .env"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        self.last_model_used = None

    def generate(self, prompt):

        strategies = [
            (
                "non-thinking + JSON output",
                True
            ),
            (
                "non-thinking without "
                "JSON response_format",
                False
            )
        ]

        for attempt, (
            strategy_name,
            structured_output
        ) in enumerate(strategies, start=1):

            if attempt == 1:
                print(
                    "DeepSeek verification: "
                    f"{strategy_name}"
                )
            else:
                print(
                    "Trying DeepSeek fallback: "
                    f"{strategy_name}..."
                )

            response = self._request(
                prompt=prompt,
                structured_output=structured_output
            )

            self.last_model_used = getattr(
                response,
                "model",
                CONTENT_VERIFIER_MODEL
            )

            choice = response.choices[0]
            content = choice.message.content
            finish_reason = choice.finish_reason

            print(
                f"Verifier model used: "
                f"{self.last_model_used}"
            )
            print(
                f"DeepSeek finish reason: "
                f"{finish_reason}"
            )

            if self._is_complete_json(
                content,
                finish_reason
            ):
                print(
                    "DeepSeek strategy succeeded: "
                    f"{strategy_name}."
                )
                return content

            if attempt == 1:
                print(
                    "DeepSeek primary response was "
                    "empty, truncated, or malformed."
                )

        raise ValueError(
            "DeepSeek verification failed: both "
            "request strategies returned empty, "
            "truncated, or malformed JSON."
        )

    def _request(
        self,
        prompt,
        structured_output
    ):

        request = {
            "model": CONTENT_VERIFIER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict but fair "
                        "educational content verifier. "
                        "Carefully check every vocabulary "
                        "word. Return only one complete "
                        "valid JSON object."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.MAX_OUTPUT_TOKENS,
            "stream": False,
            "extra_body": {
                "thinking": {
                    "type": "disabled"
                }
            }
        }

        if structured_output:
            request["response_format"] = {
                "type": "json_object"
            }

        return self.client.chat.completions.create(
            **request
        )

    @staticmethod
    def _is_complete_json(
        content,
        finish_reason
    ):

        if finish_reason == "length":
            return False

        if not isinstance(content, str):
            return False

        text = content.strip()

        if not text:
            return False

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        try:
            parsed = json.loads(text.strip())
        except json.JSONDecodeError:
            return False

        return isinstance(parsed, dict)

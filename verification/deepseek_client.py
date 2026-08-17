import os

from dotenv import load_dotenv
from openai import OpenAI

from config import CONTENT_VERIFIER_MODEL


load_dotenv()


class DeepSeekClient:

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

    def generate(
        self,
        prompt
        ):

        # =================================================
        # ATTEMPT 1
        # Thinking mode + JSON output
        # =================================================

        print(
            "DeepSeek verification: "
            "thinking mode + JSON output"
        )

        response = (
            self.client.chat.completions.create(
                model=CONTENT_VERIFIER_MODEL,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict but fair "
                            "educational content verifier. "
                            "Carefully check every vocabulary "
                            "word. Return valid JSON only."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                response_format={
                    "type": "json_object"
                },

                reasoning_effort="high",

                max_tokens=16000,

                stream=False,

                extra_body={
                    "thinking": {
                        "type": "enabled"
                    }
                }
            )
        )

        self.last_model_used = getattr(
            response,
            "model",
            CONTENT_VERIFIER_MODEL
        )

        print(
            f"Verifier model used: "
            f"{self.last_model_used}"
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        finish_reason = (
            response
            .choices[0]
            .finish_reason
        )

        print(
            f"DeepSeek finish reason: "
            f"{finish_reason}"
        )

        # -----------------------------------------
        # Good response
        # -----------------------------------------

        if (
            content
            and content.strip()
        ):

            return content


        # =================================================
        # ATTEMPT 2
        # Thinking mode WITHOUT JSON response_format
        # =================================================

        print(
            "DeepSeek returned empty content."
        )

        print(
            "Retrying with thinking mode "
            "without JSON response_format..."
        )

        response = (
            self.client.chat.completions.create(
                model=CONTENT_VERIFIER_MODEL,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict but fair "
                            "educational content verifier. "
                            "Carefully check every vocabulary "
                            "word. Return ONLY one valid JSON "
                            "object. Do not use markdown."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                reasoning_effort="high",

                max_tokens=16000,

                stream=False,

                extra_body={
                    "thinking": {
                        "type": "enabled"
                    }
                }
            )
        )

        self.last_model_used = getattr(
            response,
            "model",
            CONTENT_VERIFIER_MODEL
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        finish_reason = (
            response
            .choices[0]
            .finish_reason
        )

        print(
            f"DeepSeek retry finish reason: "
            f"{finish_reason}"
        )

        if (
            content
            and content.strip()
        ):

            print(
                "DeepSeek retry succeeded."
            )

            return content


        # =================================================
        # ATTEMPT 3
        # Non-thinking fallback
        # =================================================

        print(
            "Thinking-mode retry also "
            "returned empty content."
        )

        print(
            "Trying non-thinking fallback..."
        )

        response = (
            self.client.chat.completions.create(
                model=CONTENT_VERIFIER_MODEL,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a careful educational "
                            "content verifier. "
                            "Return valid JSON only."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                response_format={
                    "type": "json_object"
                },

                max_tokens=16000,

                stream=False,

                extra_body={
                    "thinking": {
                        "type": "disabled"
                    }
                }
            )
        )

        self.last_model_used = getattr(
            response,
            "model",
            CONTENT_VERIFIER_MODEL
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        finish_reason = (
            response
            .choices[0]
            .finish_reason
        )

        print(
            f"DeepSeek fallback finish reason: "
            f"{finish_reason}"
        )

        if (
            content
            and content.strip()
        ):

            print(
                "DeepSeek non-thinking "
                "fallback succeeded."
            )

            return content

        raise ValueError(
            "DeepSeek returned empty content "
            "after all retry attempts."
        )
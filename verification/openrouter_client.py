import os
import requests

from dotenv import load_dotenv

from config import CONTENT_VERIFIER_MODEL


load_dotenv()


class OpenRouterClient:

    API_URL = (
        "https://openrouter.ai/api/v1/chat/completions"
    )

    def __init__(self):

        self.api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found in .env"
            )

    def generate(self, prompt):

        response = requests.post(
            self.API_URL,
            headers={
                "Authorization":
                    f"Bearer {self.api_key}",

                "Content-Type":
                    "application/json"
            },
            json={
                "model":
                    CONTENT_VERIFIER_MODEL,

                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a careful "
                            "educational content verifier."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                "temperature": 0.1
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        model_used = data.get(
            "model",
            "unknown"
        )

        print(
            f"Verifier model used: {model_used}"
        )
        self.last_model_used = model_used
        return (
            data["choices"][0]
            ["message"]["content"]
        )
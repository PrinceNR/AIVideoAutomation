from google.genai import errors

from ai.gemini_client import client


class GeminiVerificationClient:

    def generate(
        self,
        contents,
        primary_model: str,
        fallback_model: str,
        task_name: str = "verification"
    ) -> dict:

        print(
            f"Gemini {task_name} model: "
            f"{primary_model}"
        )

        try:

            response = (
                client.models.generate_content(
                    model=primary_model,
                    contents=contents
                )
            )

            return {
                "status": "completed",
                "text": response.text,
                "model_used": primary_model
            }

        except errors.ServerError as error:

            if error.code != 503:
                raise

            print(
                f"{primary_model} is "
                "temporarily unavailable."
            )

            print(
                f"Trying fallback model: "
                f"{fallback_model}"
            )

        try:

            response = (
                client.models.generate_content(
                    model=fallback_model,
                    contents=contents
                )
            )

            return {
                "status": "completed",
                "text": response.text,
                "model_used": fallback_model
            }

        except errors.ServerError as error:

            if error.code != 503:
                raise

            print(
                f"Both Gemini {task_name} "
                "models are temporarily "
                "unavailable."
            )

            return {
                "status": "unavailable",
                "text": None,
                "model_used": None
            }
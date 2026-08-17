import json

from verification.deepseek_client import (
    DeepSeekClient
)


def main():

    client = DeepSeekClient()

    prompt = """
Return ONLY valid JSON.

Check whether this English vocabulary
information is correct:

Word: catch
Meaning: To hold something moving through the air.
Past form: catched

Return JSON exactly in this structure:

{
    "word": "",
    "correct": false,
    "issues": [
        {
            "field": "",
            "reason": "",
            "suggested_value": ""
        }
    ]
}
"""

    print(
        "Testing DeepSeek API...\n"
    )

    response = client.generate(
        prompt
    )

    data = json.loads(
        response
    )

    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
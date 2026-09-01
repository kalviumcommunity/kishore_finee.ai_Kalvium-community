import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from prompts import STRUCTURED_OUTPUT_SYSTEM_PROMPT

load_dotenv()

client = OpenAI(
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = os.getenv("CHAT_MODEL")

SYSTEM_PROMPT = STRUCTURED_OUTPUT_SYSTEM_PROMPT


def parse_and_validate(raw):
    """Parse JSON and verify required fields."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, "malformed JSON"

    required_fields = ["answer", "source"]

    missing = [field for field in required_fields if field not in data]

    if missing:
        return None, f"missing fields: {missing}"

    return data, None


def ask(question):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
        reasoning_effort="none",
    )

    raw = response.choices[0].message.content

    print("\nRaw response:")
    print(raw)

    data, error = parse_and_validate(raw)

    if error:
        print("\nValidation error:", error)
        return

    print("\nParsed answer:")
    print(data["answer"])

    print("\nSource:")
    print(data["source"])


if __name__ == "__main__":
    ask("What is a mutual fund?")
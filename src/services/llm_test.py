import os
import logging

from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError, RateLimitError

load_dotenv()

logging.basicConfig(level=logging.INFO)

client = OpenAI(
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

messages = [
    {
        "role": "system",
        "content": "You are a concise assistant. Give only the final answer."
    },
    {
        "role": "user",
        "content": "Say hello in one sentence."
    }
]

logging.info("REQUEST: %s", messages)

try:
    response = client.chat.completions.create(
        model=os.getenv("CHAT_MODEL"),
        messages=messages,
        reasoning_effort="none"
    )

    answer = response.choices[0].message.content

    logging.info("RESPONSE: %s", answer)
    logging.info("USAGE: %s", response.usage)

    print("\nAssistant:")
    print(answer)

except AuthenticationError:
    print("Auth failed (401): check GROQ_API_KEY in your .env")

except RateLimitError:
    print("Rate limited (429): check Groq quota/rate limit and retry.")

except Exception as error:
    print(f"API request failed: {error}")
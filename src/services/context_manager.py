import os

from dotenv import load_dotenv
from openai import OpenAI

from src.services.token_usage import count_tokens

load_dotenv()

client = OpenAI(
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = os.getenv("CHAT_MODEL")

SYSTEM_PROMPT = (
    "You are a concise financial information assistant for FInee.ai. "
    "Answer in 2-3 sentences maximum. "
    "Answer factually and do not provide personalized financial advice."
)

# Small enough to demonstrate trimming, but large enough
# to preserve multiple conversation turns.
MAX_HISTORY_TOKENS = 250


def total_tokens(messages):
    """Count total tokens across all message contents."""
    return sum(count_tokens(message["content"]) for message in messages)


def trim_history(messages, budget=MAX_HISTORY_TOKENS):
    """
    Remove the oldest complete user/assistant turns
    while keeping the system prompt and staying within budget.
    """
    while total_tokens(messages) > budget and len(messages) > 3:
        # Remove oldest user message
        messages.pop(1)

        # Remove the assistant response belonging to that user message
        messages.pop(1)


history = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }
]


def ask(user_message):
    """Send a question while maintaining and trimming conversation history."""

    history.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    print(f"\nHistory tokens before request: {total_tokens(history)}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=history,
        reasoning_effort="none",
    )

    answer = response.choices[0].message.content

    history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    # Keep the stored history within the token budget.
    trim_history(history)

    print(f"User: {user_message}")
    print(f"Assistant: {answer}")
    print(f"History tokens after trimming: {total_tokens(history)}")
    print(f"Messages currently stored: {len(history)}")

    return answer


if __name__ == "__main__":
    ask("What is a mutual fund?")
    ask("What are its main benefits?")
    ask("How is a mutual fund different from buying one stock?")
    ask("Why is diversification important?")
    ask("What does a fund manager do?")
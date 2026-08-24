import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = os.getenv("CHAT_MODEL")


# System prompt defines the assistant's role and rules
system_prompt = """
You are a financial information assistant for FInee.ai.

Rules:
- Give concise and factual answers.
- Do not invent financial information.
- If the information is not provided, say "I don't know."
- Do not provide personalized financial advice.
"""

prompts = [
    "What is a mutual fund?",
    "Explain mutual funds in one sentence.",
]


for prompt in prompts:

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        reasoning_effort="none"
    )

    answer = response.choices[0].message.content

    print("\nUSER:", prompt)
    print("ASSISTANT:", answer)
    print("-" * 60)
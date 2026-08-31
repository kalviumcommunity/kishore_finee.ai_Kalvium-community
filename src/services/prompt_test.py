import os
from dotenv import load_dotenv
from openai import OpenAI
from prompts import FINANCIAL_INFO_SYSTEM_PROMPT

load_dotenv()

client = OpenAI(
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = os.getenv("CHAT_MODEL")

system_prompt = FINANCIAL_INFO_SYSTEM_PROMPT

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
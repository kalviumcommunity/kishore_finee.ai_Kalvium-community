import os

from dotenv import load_dotenv
from openai import OpenAI
from prompts import CONVERSATIONAL_SYSTEM_PROMPT

load_dotenv()

client = OpenAI(
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = os.getenv("CHAT_MODEL")

messages = [
    {
        "role": "system",
        "content": CONVERSATIONAL_SYSTEM_PROMPT,
    },
    {
        "role": "user",
        "content": (
            "Explain why diversification is important in investing."
        ),
    },
]


print("=" * 70)
print("TEMPERATURE COMPARISON")
print("=" * 70)

for temperature in [0.0, 1.0]:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        reasoning_effort="none",
    )

    print(f"\nTemperature = {temperature}")
    print(response.choices[0].message.content)


print("\n" + "=" * 70)
print("MAX TOKENS")
print("=" * 70)

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    temperature=0.1,
    max_tokens=80,
    reasoning_effort="none",
)

print("\nmax_tokens = 80")
print(response.choices[0].message.content)


print("\n" + "=" * 70)
print("STOP SEQUENCE")
print("=" * 70)

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    temperature=0.1,
    max_tokens=150,
    stop=["END"],
    reasoning_effort="none",
)

print("\nstop = ['END']")
print(response.choices[0].message.content)


print("\n" + "=" * 70)
print("TOP P")
print("=" * 70)

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    temperature=0.1,
    top_p=0.5,
    max_tokens=150,
    reasoning_effort="none",
)

print("\ntop_p = 0.5")
print(response.choices[0].message.content)
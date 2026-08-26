#!/usr/bin/env python3
"""Demonstration script comparing LLM output consistency at temperature 0.0 vs 1.0."""

import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import settings
from src.services.llm import generate_answer, LLMConfigurationError, LLMServiceError


# A typical financial RAG query context and question
MOCK_CONTEXT = """
Global Horizon Growth Fund (Class A) Year-End Report 2025:
- Total Assets Under Management: $1.24 Billion USD.
- Annualized Return (since inception in 2018): 8.42% net of fees.
- 1-Year Performance (2025): 12.15% driven by technology and industrial sectors.
- Net Asset Value (NAV) as of Dec 31, 2025: $14.22 per share.
- Risk Profile: Moderate-High. Primary risk factors include equity market volatility and interest rate sensitivity.
- Fund Manager: Sarah Jenkins.
"""

MOCK_QUESTION = "What was the annualized return of the Global Horizon Growth Fund since its inception in 2018, and what is its risk profile?"


async def run_demonstration():
    print("======================================================================")
    print("      FInee.ai - Temperature & Output Consistency Demonstration       ")
    print("======================================================================\n")

    # Check for API key
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please configure OPENAI_API_KEY in your local .env file or system environment.")
        print("\nNote: When API access is available, this script makes 6 calls to compare:")
        print("  - 3 runs at Temperature = 0.0 (expecting high consistency/identity)")
        print("  - 3 runs at Temperature = 1.0 (expecting potential variations/stylistic differences)")
        print("\nExiting demonstration.")
        return

    print("Running demonstration with:")
    print(f"  API Base URL: {settings.OPENAI_BASE_URL or 'https://api.openai.com/v1'}")
    print(f"  Chat Model  : {settings.CHAT_MODEL or 'gpt-4o-mini'}")
    print(f"  Max Tokens  : {settings.LLM_MAX_TOKENS}")
    print(f"  Top P       : {settings.LLM_TOP_P}")
    print("\n----------------------------------------------------------------------")
    print(f"Input Question: {MOCK_QUESTION}")
    print("----------------------------------------------------------------------\n")

    # 1. Run at temperature 0.0
    print("Executing 3 runs at Temperature = 0.0 (Strictly Factual & Consistent)...")
    temp_low = 0.0
    low_outputs = []
    
    for i in range(1, 4):
        print(f"  [Temp {temp_low}] Run #{i}...", end="", flush=True)
        try:
            output = await generate_answer(
                question=MOCK_QUESTION,
                context=MOCK_CONTEXT,
                temperature=temp_low,
            )
            low_outputs.append(output)
            print(" Done.")
        except Exception as e:
            print(f" Failed: {e}")
            return

    print("\n--- Temperature 0.0 Results ---")
    all_low_identical = len(set(low_outputs)) == 1
    for idx, out in enumerate(low_outputs, 1):
        print(f"\n[Run #{idx} Output]:\n{out}")
    print(f"\nConsistency Check: All 3 runs are {'IDENTICAL' if all_low_identical else 'DIFFERENT'}.\n")

    # 2. Run at temperature 1.0
    print("Executing 3 runs at Temperature = 1.0 (Creative & Varied)...")
    temp_high = 1.0
    high_outputs = []

    for i in range(1, 4):
        print(f"  [Temp {temp_high}] Run #{i}...", end="", flush=True)
        try:
            output = await generate_answer(
                question=MOCK_QUESTION,
                context=MOCK_CONTEXT,
                temperature=temp_high,
            )
            high_outputs.append(output)
            print(" Done.")
        except Exception as e:
            print(f" Failed: {e}")
            return

    print("\n--- Temperature 1.0 Results ---")
    all_high_identical = len(set(high_outputs)) == 1
    for idx, out in enumerate(high_outputs, 1):
        print(f"\n[Run #{idx} Output]:\n{out}")
    print(f"\nConsistency Check: All 3 runs are {'IDENTICAL' if all_high_identical else 'DIFFERENT'}.")
    
    print("\n======================================================================")
    print("Conclusion:")
    if all_low_identical and not all_high_identical:
        print("Success! Low temperature produced completely consistent results across runs,")
        print("whereas high temperature (1.0) led to variations in wording/structure.")
    elif all_low_identical:
        print("Both temperatures produced consistent results. In some cases, gpt-4o-mini/smaller")
        print("models are highly constrained by the grounded context prompts even at high temperature.")
    else:
        print("Completed successfully. Compare the outputs above to evaluate style/variations.")
    print("======================================================================\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_demonstration())
    except KeyboardInterrupt:
        print("\nDemonstration interrupted.")

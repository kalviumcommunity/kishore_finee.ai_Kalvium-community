"""Demonstration of Token-Aware Chunk Sizing & Overlap (Concept 13).

This script demonstrates:
1. Sizing chunks strictly by tokens using tiktoken (cl100k_base).
2. Controlled overlap between adjacent chunks.
3. Demonstration of boundary context preservation (with and without overlap).
4. Sizing and overlap justification for the FInee.ai model context budget.
5. JSON evaluation report generation.
"""

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Any, Dict, List

import tiktoken

from src.ingestion.chunking import (
    DEFAULT_ENCODING,
    fixed_chunks,
    token_chunks,
    token_chunks_with_metadata,
)
from src.ingestion.document_loader import load_text


DEFAULT_OUTPUT_PATH = Path("outputs/evaluations/token_chunking_results.json")


def compare_token_vs_char_sizing(text: str, encoding_name: str = DEFAULT_ENCODING) -> Dict[str, Any]:
    """Compare fixed character chunking with token-aware chunking."""
    enc = tiktoken.get_encoding(encoding_name)

    # Character-based fixed chunks (100 chars, 20 overlap)
    char_chunks_list = fixed_chunks(text, size=100, overlap=20)
    char_chunk_tokens = [len(enc.encode(c)) for c in char_chunks_list]

    # Token-based chunks (400 tokens, 60 overlap)
    tok_chunks_list = token_chunks(text, size=400, overlap=60, encoding_name=encoding_name)
    tok_chunk_tokens = [len(enc.encode(c)) for c in tok_chunks_list]

    return {
        "character_chunking": {
            "size_chars": 100,
            "overlap_chars": 20,
            "chunk_count": len(char_chunks_list),
            "min_tokens_per_chunk": min(char_chunk_tokens) if char_chunk_tokens else 0,
            "max_tokens_per_chunk": max(char_chunk_tokens) if char_chunk_tokens else 0,
            "avg_tokens_per_chunk": sum(char_chunk_tokens) // len(char_chunk_tokens) if char_chunk_tokens else 0,
        },
        "token_aware_chunking": {
            "size_tokens": 400,
            "overlap_tokens": 60,
            "chunk_count": len(tok_chunks_list),
            "min_tokens_per_chunk": min(tok_chunk_tokens) if tok_chunk_tokens else 0,
            "max_tokens_per_chunk": max(tok_chunk_tokens) if tok_chunk_tokens else 0,
            "avg_tokens_per_chunk": sum(tok_chunk_tokens) // len(tok_chunk_tokens) if tok_chunk_tokens else 0,
        },
    }


def compare_overlap_variations(text: str, chunk_size: int = 400, overlaps: List[int] = None, encoding_name: str = DEFAULT_ENCODING) -> List[Dict[str, Any]]:
    """Compare chunk counts and token overhead across different overlap values."""
    if overlaps is None:
        overlaps = [0, 40, 60, 100]

    enc = tiktoken.get_encoding(encoding_name)
    base_tokens = len(enc.encode(text))
    results = []

    for ov in overlaps:
        chunks = token_chunks(text, size=chunk_size, overlap=ov, encoding_name=encoding_name)
        total_tokens_stored = sum(len(enc.encode(c)) for c in chunks)
        duplicate_ratio = (
            ((total_tokens_stored - base_tokens) / base_tokens * 100.0)
            if base_tokens > 0 and total_tokens_stored > base_tokens
            else 0.0
        )

        results.append(
            {
                "chunk_size_tokens": chunk_size,
                "overlap_tokens": ov,
                "overlap_percentage": round((ov / chunk_size) * 100, 1),
                "chunk_count": len(chunks),
                "total_tokens_stored": total_tokens_stored,
                "duplicate_token_overhead_pct": round(duplicate_ratio, 2),
            }
        )

    return results


def demonstrate_boundary_context() -> Dict[str, Any]:
    """Demonstrate how overlap preserves complete ideas that sit across chunk boundaries."""
    # A realistic compliance clause where cutting in half destroys semantic meaning
    sample_text = (
        "FInee.ai Compliance Advisory Memo: Section 4.2 Regulatory Fee Guidelines. "
        "Advisors must ensure that portfolio fee reductions comply strictly with SEC Rule 206(4)-1. "
        "Specifically, clients are eligible for a 0.50% advisory fee discount only if their aggregate qualifying "
        "asset balance across linked family accounts exceeds $250,000 as of the quarter-end evaluation date. "
        "Accounts failing to maintain this threshold will revert to standard asset management fee schedules without exception. "
        "All communications regarding fee tiers must retain audit logs for seven years."
    )

    enc = tiktoken.get_encoding(DEFAULT_ENCODING)

    # Chunk with NO overlap (overlap = 0)
    no_overlap_chunks = token_chunks(sample_text, size=35, overlap=0)
    # Chunk WITH controlled overlap (overlap = 15 tokens)
    with_overlap_chunks = token_chunks(sample_text, size=35, overlap=15)

    target_query = "What asset balance and evaluation timing are required for the 0.50% fee discount?"

    # Check whether the complete condition (0.50%, $250,000, and quarter-end evaluation date) appears together in a single chunk
    def has_complete_answer(chunk_list: List[str]) -> bool:
        for c in chunk_list:
            if "0.50%" in c and "$250,000" in c and "quarter-end evaluation date" in c:
                return True
        return False

    return {
        "text": sample_text,
        "total_tokens": len(enc.encode(sample_text)),
        "target_query": target_query,
        "required_facts": ["0.50% advisory fee discount", "$250,000 qualifying balance", "quarter-end evaluation date"],
        "no_overlap": {
            "chunk_size": 35,
            "overlap": 0,
            "chunks": no_overlap_chunks,
            "intact_answer_found": has_complete_answer(no_overlap_chunks),
            "explanation": (
                "With overlap=0, the boundary cut splits the clause at 'as of the'. "
                "Chunk 2 contains '0.50%' and '$250,000' but misses 'quarter-end evaluation date'. "
                "Chunk 3 starts with 'quarter-end evaluation date' but misses the fee discount and amount. "
                "Neither chunk contains the complete fact, causing compliance retrieval to return fragmented info."
            ),
        },
        "with_overlap": {
            "chunk_size": 35,
            "overlap": 15,
            "chunks": with_overlap_chunks,
            "intact_answer_found": has_complete_answer(with_overlap_chunks),
            "explanation": (
                "With overlap=15, the boundary tokens repeat. Chunk 3 contains '0.50% advisory fee discount', "
                "'$250,000', AND 'quarter-end evaluation date' intact in a single chunk, ensuring accurate retrieval."
            ),
        },
    }


def get_model_budget_justification() -> Dict[str, Any]:
    """Provide the technical justification for the chosen chunk size and overlap settings."""
    return {
        "recommended_settings": {
            "chunk_size_tokens": 400,
            "overlap_tokens": 60,
            "overlap_percentage": "15%",
            "tokenizer": "cl100k_base (tiktoken)",
        },
        "context_window_budget": {
            "model": "LLaMA-3-70B / Groq (8,192 context window minimum) & GPT-4o-mini",
            "top_k_retrieval_chunks": 5,
            "retrieved_context_tokens": 5 * 400,  # 2,000 tokens
            "system_prompt_and_guardrails_tokens": 350,
            "user_query_and_history_tokens": 400,
            "model_response_generation_budget": 500,
            "total_budget_used": 3250,
            "context_window_limit": 8192,
            "headroom_remaining": 8192 - 3250,
        },
        "tradeoff_analysis": {
            "chunk_size_400_tokens": (
                "400 tokens (~300 words / 2-3 financial paragraphs) provides enough semantic density "
                "for embedding models while keeping chunks focused on a single compliance topic."
            ),
            "overlap_60_tokens": (
                "60 tokens (~45 words / 2 sentences) ensures compound sentences, financial conditions, "
                "and regulatory disclaimers spanning chunk boundaries are preserved intact in at least one chunk."
            ),
            "cost_and_storage_impact": (
                "At 15% overlap, embedding cost and storage increase by only ~15-18%, a modest trade-off for "
                "eliminating boundary-cut retrieval failures."
            ),
        },
    }


def run_demonstration(output_path: Path = DEFAULT_OUTPUT_PATH) -> Dict[str, Any]:
    """Execute all demonstration tasks and return structured report."""
    print("=" * 70)
    print("FInee.ai — TOKEN-AWARE CHUNK SIZING & OVERLAP DEMO (Concept 13)")
    print("=" * 70)

    # 1. Load sample data
    sample_files = [
        Path("README.md"),
        Path("data/sample/sample.txt"),
        Path("data/sample/sample.md"),
    ]

    corpus_text = ""
    for sf in sample_files:
        if sf.exists():
            corpus_text += load_text(sf) + "\n\n"

    if not corpus_text.strip():
        corpus_text = (
            "FInee.ai is a compliance-grounded financial advisory platform. "
            "It assists financial advisors in answering client queries while maintaining strict adherence "
            "to regulatory guidelines, SEC filings, and fund disclosures."
        )

    # Task 1: Size by tokens
    print("\n[TASK 1] Sizing by Tokens vs Characters")
    print("-" * 70)
    task1_result = compare_token_vs_char_sizing(corpus_text)
    print(f"Corpus Length: {len(corpus_text)} characters")
    print(f"Character Chunking (size=100, ov=20): {task1_result['character_chunking']['chunk_count']} chunks, "
          f"tokens/chunk range: [{task1_result['character_chunking']['min_tokens_per_chunk']} - {task1_result['character_chunking']['max_tokens_per_chunk']}]")
    print(f"Token Chunking     (size=400, ov=60): {task1_result['token_aware_chunking']['chunk_count']} chunks, "
          f"tokens/chunk: {task1_result['token_aware_chunking']['avg_tokens_per_chunk']} avg")

    # Task 2: Controlled Overlap
    print("\n[TASK 2] Controlled Overlap Variations (Cost vs Chunk Count)")
    print("-" * 70)
    task2_result = compare_overlap_variations(corpus_text, chunk_size=400, overlaps=[0, 40, 60, 100])
    for row in task2_result:
        print(f"  Overlap: {row['overlap_tokens']} tokens ({row['overlap_percentage']}%) | "
              f"Chunks: {row['chunk_count']} | Total Stored: {row['total_tokens_stored']} tokens | "
              f"Duplication Overhead: +{row['duplicate_token_overhead_pct']}%")

    # Task 3: Boundary Context Preservation
    print("\n[TASK 3] Boundary Context Preservation Demonstration")
    print("-" * 70)
    task3_result = demonstrate_boundary_context()
    print(f"Target Query: \"{task3_result['target_query']}\"")
    print(f"Required Facts: {', '.join(task3_result['required_facts'])}")
    print(f"Without Overlap (overlap=0): Complete answer found in single chunk? {task3_result['no_overlap']['intact_answer_found']}")
    for idx, ch in enumerate(task3_result['no_overlap']['chunks']):
        print(f"  [No Overlap Chunk {idx+1}]: \"{ch}\"")
    print(f"With Overlap (overlap=15):   Complete answer found in single chunk? {task3_result['with_overlap']['intact_answer_found']}")
    for idx, ch in enumerate(task3_result['with_overlap']['chunks']):
        print(f"  [With Overlap Chunk {idx+1}]: \"{ch}\"")

    # Task 4: Justification
    print("\n[TASK 4] Sizing & Overlap Justification for FInee.ai")
    print("-" * 70)
    task4_result = get_model_budget_justification()
    print(f"Recommended Size: {task4_result['recommended_settings']['chunk_size_tokens']} tokens")
    print(f"Recommended Overlap: {task4_result['recommended_settings']['overlap_tokens']} tokens ({task4_result['recommended_settings']['overlap_percentage']})")
    print(f"Context Window Budget: {task4_result['context_window_budget']['total_budget_used']} tokens total out of 8,192 (Top-K=5)")

    report = {
        "concept": "Concept 13: Token-Aware Chunk Sizing & Overlap",
        "task1_sizing_comparison": task1_result,
        "task2_overlap_variations": task2_result,
        "task3_boundary_preservation": task3_result,
        "task4_model_budget_justification": task4_result,
    }

    # Task 5: Save JSON report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[TASK 5] Evaluation output saved to: {output_path}")
    print("=" * 70)

    return report


def main():
    parser = ArgumentParser(description="Demonstrate Token-Aware Chunk Sizing & Overlap")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to save output evaluation JSON",
    )
    args = parser.parse_args()
    run_demonstration(output_path=args.output)


if __name__ == "__main__":
    main()

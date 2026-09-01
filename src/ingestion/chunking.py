"""Document chunking strategies for FInee.ai, including token-aware chunking."""

from pathlib import Path
import re
from typing import Any, Dict, List

import tiktoken

from src.ingestion.document_loader import load_text


DEFAULT_ENCODING = "cl100k_base"
DEFAULT_TOKEN_CHUNK_SIZE = 400
DEFAULT_TOKEN_CHUNK_OVERLAP = 60


# 1. Fixed-size chunking (character-based)
def fixed_chunks(text: str, size: int = 100, overlap: int = 20) -> List[str]:
    """Split text by fixed character count."""
    if size <= 0:
        raise ValueError(f"Chunk size must be greater than 0, got {size}")
    if overlap < 0 or overlap >= size:
        raise ValueError(f"Overlap must be in range [0, size), got {overlap}")

    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start : start + size].strip()

        if chunk:
            chunks.append(chunk)

        start += size - overlap

    return chunks


# 2. Sentence chunking
def sentence_chunks(text: str, max_size: int = 150) -> List[str]:
    """Split text by sentence boundaries up to max_size characters."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        if current and len(current) + len(sentence) + 1 > max_size:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()

    if current:
        chunks.append(current)

    return chunks


# 3. Paragraph chunking
def paragraph_chunks(text: str) -> List[str]:
    """Split text by double newlines into paragraphs."""
    paragraphs = re.split(r"\n\s*\n", text.strip())

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


# 4. Recursive chunking (character-based fallback)
def recursive_chunks(text: str, max_size: int = 150) -> List[str]:
    """Recursively split text by paragraphs then sentences to stay under max_size characters."""
    if len(text.strip()) <= max_size:
        return [text.strip()]

    paragraphs = paragraph_chunks(text)

    if len(paragraphs) > 1:
        chunks = []

        for paragraph in paragraphs:
            if len(paragraph) <= max_size:
                chunks.append(paragraph)
            else:
                chunks.extend(
                    sentence_chunks(paragraph, max_size)
                )

        return chunks

    return sentence_chunks(text, max_size)


# 5. Token-Aware Chunking with Controlled Overlap (Concept 13)
def token_chunks(
    text: str,
    size: int = DEFAULT_TOKEN_CHUNK_SIZE,
    overlap: int = DEFAULT_TOKEN_CHUNK_OVERLAP,
    encoding_name: str = DEFAULT_ENCODING,
) -> List[str]:
    """Split text into chunks sized by token count with controlled token overlap.

    Args:
        text: Input raw or cleaned text to chunk.
        size: Target chunk size measured in tokens (default: 400).
        overlap: Number of tokens to repeat between adjacent chunks (default: 60).
        encoding_name: tiktoken encoding name (default: "cl100k_base").

    Returns:
        List of decoded text chunks.
    """
    if size <= 0:
        raise ValueError(f"Chunk size must be greater than 0, got {size}")
    if overlap < 0:
        raise ValueError(f"Overlap cannot be negative, got {overlap}")
    if overlap >= size:
        raise ValueError(f"Overlap ({overlap}) must be strictly less than chunk size ({size})")

    if not text or not text.strip():
        return []

    enc = tiktoken.get_encoding(encoding_name)
    toks = enc.encode(text)

    if not toks:
        return []

    chunks = []
    i = 0
    step = size - overlap

    while i < len(toks):
        chunk_tokens = toks[i : i + size]
        decoded = enc.decode(chunk_tokens).strip()
        if decoded:
            chunks.append(decoded)
        i += step

    return chunks


def token_chunks_with_metadata(
    text: str,
    size: int = DEFAULT_TOKEN_CHUNK_SIZE,
    overlap: int = DEFAULT_TOKEN_CHUNK_OVERLAP,
    encoding_name: str = DEFAULT_ENCODING,
) -> List[Dict[str, Any]]:
    """Split text into token chunks and return detailed metadata for each chunk.

    Args:
        text: Input text to chunk.
        size: Target chunk size in tokens.
        overlap: Number of overlapping tokens between adjacent chunks.
        encoding_name: tiktoken encoding name.

    Returns:
        List of dicts containing index, text, token_count, and token spans.
    """
    if size <= 0:
        raise ValueError(f"Chunk size must be greater than 0, got {size}")
    if overlap < 0:
        raise ValueError(f"Overlap cannot be negative, got {overlap}")
    if overlap >= size:
        raise ValueError(f"Overlap ({overlap}) must be strictly less than chunk size ({size})")

    if not text or not text.strip():
        return []

    enc = tiktoken.get_encoding(encoding_name)
    toks = enc.encode(text)

    if not toks:
        return []

    chunks = []
    i = 0
    step = size - overlap
    chunk_index = 0

    while i < len(toks):
        chunk_tokens = toks[i : i + size]
        decoded = enc.decode(chunk_tokens).strip()
        if decoded:
            chunks.append(
                {
                    "index": chunk_index,
                    "text": decoded,
                    "token_count": len(chunk_tokens),
                    "start_token_idx": i,
                    "end_token_idx": min(i + size, len(toks)),
                }
            )
            chunk_index += 1
        i += step

    return chunks


def show_strategy(name: str, chunks: List[str], is_token_strategy: bool = False, encoding_name: str = DEFAULT_ENCODING) -> None:
    """Print summary statistics and first chunk preview for a chunking strategy."""
    if not chunks:
        print(f"{name}: No chunks")
        return

    if is_token_strategy:
        enc = tiktoken.get_encoding(encoding_name)
        token_sizes = [len(enc.encode(c)) for c in chunks]
        avg_tokens = sum(token_sizes) // len(token_sizes)
        print(f"\n{name}")
        print(f"  Number of chunks : {len(chunks)}")
        print(f"  Average size    : {avg_tokens} tokens")
    else:
        sizes = [len(chunk) for chunk in chunks]
        average = sum(sizes) // len(sizes)
        print(f"\n{name}")
        print(f"  Number of chunks : {len(chunks)}")
        print(f"  Average size    : {average} characters")

    print("  First chunk:")
    print(f'  "{chunks[0][:120]}"')


def main():
    data_dir = Path("data")

    print("=" * 60)
    print("FInee.ai - DOCUMENT CHUNKING & TOKEN-AWARE SIZING")
    print("=" * 60)

    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in [".pdf", ".txt", ".md", ".html", ".htm"]:
            continue

        try:
            text = load_text(path)

            if not text.strip():
                continue

            print("\n" + "-" * 60)
            print(f"Document: {path.name}")
            print("-" * 60)

            # Character-based chunking strategies
            fixed = fixed_chunks(text)
            sentence = sentence_chunks(text)
            paragraph = paragraph_chunks(text)
            recursive = recursive_chunks(text)

            # Token-aware chunking strategy (Concept 13)
            token_based = token_chunks(text, size=400, overlap=60)

            show_strategy("1. Fixed-size (Char)", fixed)
            show_strategy("2. Sentence (Char)", sentence)
            show_strategy("3. Paragraph (Char)", paragraph)
            show_strategy("4. Recursive (Char)", recursive)
            show_strategy("5. Token-Aware (size=400, overlap=60)", token_based, is_token_strategy=True)

        except Exception as error:
            print(f"Could not process {path.name}: {error}")

    print("\n" + "=" * 60)
    print("RECOMMENDED STRATEGY FOR LLM RAG PIPELINES")
    print("=" * 60)
    print("Token-Aware Chunking (Size: 400 tokens, Overlap: 60 tokens / 15%)")
    print("Reason: Sizes directly in LLM tokens for budget adherence,")
    print("and preserves boundary context across chunk edges.")
    print("=" * 60)


if __name__ == "__main__":
    main()
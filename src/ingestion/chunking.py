"""Document chunking strategies for FInee.ai."""

from pathlib import Path
import re

from src.ingestion.document_loader import load_text


# 1. Fixed-size chunking
def fixed_chunks(text, size=100, overlap=20):
    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start:start + size].strip()

        if chunk:
            chunks.append(chunk)

        start += size - overlap

    return chunks


# 2. Sentence chunking
def sentence_chunks(text, max_size=150):
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
def paragraph_chunks(text):
    paragraphs = re.split(r"\n\s*\n", text.strip())

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


# 4. Recursive chunking
def recursive_chunks(text, max_size=150):
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


def show_strategy(name, chunks):
    if not chunks:
        print(f"{name}: No chunks")
        return

    sizes = [len(chunk) for chunk in chunks]
    average = sum(sizes) // len(sizes)

    print(f"\n{name}")
    print(f"  Number of chunks : {len(chunks)}")
    print(f"  Average size    : {average} characters")

    print("  First chunk:")
    print(f"  \"{chunks[0][:120]}\"")


def main():

    data_dir = Path("data")

    print("=" * 60)
    print("FInee.ai - DOCUMENT CHUNKING")
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

            # Four chunking strategies
            fixed = fixed_chunks(text)
            sentence = sentence_chunks(text)
            paragraph = paragraph_chunks(text)
            recursive = recursive_chunks(text)

            show_strategy("1. Fixed-size", fixed)
            show_strategy("2. Sentence", sentence)
            show_strategy("3. Paragraph", paragraph)
            show_strategy("4. Recursive", recursive)

        except Exception as error:
            print(f"Could not process {path.name}: {error}")

    print("\n" + "=" * 60)
    print("RECOMMENDED STRATEGY")
    print("=" * 60)
    print("Recursive chunking")
    print("Reason: It keeps meaningful boundaries while")
    print("preventing chunks from becoming too large.")
    print("=" * 60)


if __name__ == "__main__":
    main()
"""End-to-end document ingestion and validation for FInee.ai."""

from pathlib import Path

from src.ingestion.document_loader import load_text
from src.ingestion.chunking import recursive_chunks


SUPPORTED_FORMATS = {".pdf", ".txt", ".md", ".html", ".htm"}


def clean_text(text):
    """Basic text cleaning."""
    return " ".join(text.split())


def add_metadata(source, chunks):
    """Attach source and chunk position metadata."""
    tagged_chunks = []

    for index, chunk in enumerate(chunks):
        tagged_chunks.append({
            "text": chunk,
            "metadata": {
                "source": source,
                "chunk_index": index,
            }
        })

    return tagged_chunks


def ingest(folder):
    """Run the complete ingestion pipeline."""

    folder = Path(folder)

    files = [
        path
        for path in folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_FORMATS
    ]

    documents_processed = 0
    all_chunks = []
    failures = []

    for path in files:
        try:
            # 1. Load document
            text = load_text(path)

            # 2. Clean text
            text = clean_text(text)

            if not text:
                raise ValueError("Document contains no text")

            # 3. Chunk document
            chunks = recursive_chunks(text)

            # 4. Add metadata
            tagged_chunks = add_metadata(path.name, chunks)

            all_chunks.extend(tagged_chunks)
            documents_processed += 1

            print(
                f"OK   {path.name} -> "
                f"{len(tagged_chunks)} chunks"
            )

        except Exception as error:
            failures.append((path.name, str(error)))

            print(
                f"FAIL {path.name} -> {error}"
            )

    return files, documents_processed, all_chunks, failures


def validate(files, documents_processed, chunks, failures):
    """Validate that no document was silently dropped."""

    print("\n" + "=" * 60)
    print("INGESTION VALIDATION")
    print("=" * 60)

    print(f"Total files       : {len(files)}")
    print(f"Documents loaded  : {documents_processed}")
    print(f"Total chunks      : {len(chunks)}")
    print(f"Failures          : {len(failures)}")

    # Important validation
    assert (
        documents_processed + len(failures) == len(files)
    ), "A document was silently dropped!"

    if failures:
        print("\nFailed documents:")
        for name, error in failures:
            print(f"- {name}: {error}")
    else:
        print("\nNo ingestion failures.")

    if chunks:
        print("\nSample chunk:")
        print(chunks[0]["text"][:150])

        print("\nSample metadata:")
        print(chunks[0]["metadata"])

    print("\nValidation successful.")


def main():
    print("=" * 60)
    print("FInee.ai - CORPUS INGESTION PIPELINE")
    print("=" * 60)

    files, documents, chunks, failures = ingest("data")

    validate(
        files,
        documents,
        chunks,
        failures
    )


if __name__ == "__main__":
    main()
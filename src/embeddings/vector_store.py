"""Vector database indexing for FInee.ai."""

from pathlib import Path
import sys

import chromadb


# Allow imports from project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

DB_PATH = "data/chroma_db"
COLLECTION_NAME = "finee_documents"


# ------------------------------------------------------------
# Create / open ChromaDB collection
# ------------------------------------------------------------

def get_collection():
    """Create or open the FInee.ai vector collection."""

    client = chromadb.PersistentClient(path=DB_PATH)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "FInee.ai financial document embeddings"
        }
    )

    return collection


# ------------------------------------------------------------
# Convert chunk into vector database record
# ------------------------------------------------------------

def to_vector_record(chunk):
    """Convert a chunk into a vector database record."""

    metadata = chunk.get("metadata", {})

    return {
        "id": chunk["id"],
        "text": chunk["text"],
        "embedding": chunk["embedding"],
        "metadata": {
            "source": metadata.get("source", "unknown"),
            "chunk_index": metadata.get("chunk_index", 0),
        },
    }


# ------------------------------------------------------------
# Index embeddings
# ------------------------------------------------------------

def index_chunks(chunks):
    """Store chunk embeddings, text and metadata in ChromaDB."""

    collection = get_collection()

    if not chunks:
        print("No chunks available for indexing.")
        return collection

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for chunk in chunks:

        record = to_vector_record(chunk)

        ids.append(record["id"])
        documents.append(record["text"])
        embeddings.append(record["embedding"])
        metadatas.append(record["metadata"])

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return collection


# ------------------------------------------------------------
# Validate indexed count
# ------------------------------------------------------------

def validate_index(collection, expected_count):
    """Verify that all chunks were indexed."""

    indexed_count = collection.count()

    print("\n" + "=" * 60)
    print("INDEXING VALIDATION")
    print("=" * 60)

    print(f"Expected chunks : {expected_count}")
    print(f"Indexed chunks  : {indexed_count}")

    if indexed_count != expected_count:
        raise AssertionError(
            "Indexed count does not match expected chunk count."
        )

    print("Status          : SUCCESS")


# ------------------------------------------------------------
# Spot check
# ------------------------------------------------------------

def spot_check(collection, chunk_id):
    """Read one record from ChromaDB and verify it."""

    result = collection.get(
        ids=[chunk_id],
        include=[
            "documents",
            "metadatas",
            "embeddings"
        ]
    )

    if not result["ids"]:
        raise ValueError(f"Chunk not found: {chunk_id}")

    print("\n" + "=" * 60)
    print("SPOT CHECK")
    print("=" * 60)

    print("ID       :", result["ids"][0])
    print("Source   :", result["metadatas"][0]["source"])
    print("Chunk    :", result["metadatas"][0]["chunk_index"])
    print("Text     :", result["documents"][0][:120])

    vector = result["embeddings"][0]

    print("Vector dimensions :", len(vector))
    print("Spot check passed.")


# ------------------------------------------------------------
# Sample embedded chunks
# ------------------------------------------------------------

def create_sample_chunks():
    """
    Sample chunks containing pre-generated embeddings.

    These embeddings match the example embeddings used
    in src/embeddings/similarity.py.
    """

    return [
        {
            "id": "sample-fund-0",
            "text": "Mutual funds pool money from multiple investors.",
            "embedding": [0.88, 0.78, 0.12],
            "metadata": {
                "source": "sample-fund.md",
                "chunk_index": 0,
            },
        },
        {
            "id": "sample-equity-1",
            "text": "Equity funds invest mainly in company shares.",
            "embedding": [0.70, 0.75, 0.20],
            "metadata": {
                "source": "sample-equity.md",
                "chunk_index": 1,
            },
        },
        {
            "id": "sample-expenses-2",
            "text": "A mutual fund's expense ratio represents operating expenses.",
            "embedding": [0.30, 0.20, 0.90],
            "metadata": {
                "source": "sample-expenses.md",
                "chunk_index": 2,
            },
        },
        {
            "id": "sample-debt-3",
            "text": "Interest rates can affect debt fund performance.",
            "embedding": [0.20, 0.30, 0.85],
            "metadata": {
                "source": "sample-debt.md",
                "chunk_index": 3,
            },
        },
    ]


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    """Run the FInee.ai embedding indexing demonstration."""

    print("=" * 60)
    print("FInee.ai - EMBEDDING INDEXING")
    print("=" * 60)

    # These chunks already contain embeddings.
    chunks = create_sample_chunks()

    print(f"\nChunks prepared : {len(chunks)}")

    # Store them in ChromaDB.
    collection = index_chunks(chunks)

    print("Chunks indexed successfully.")

    # Verify indexed count.
    validate_index(
        collection,
        expected_count=len(chunks)
    )

    # Read one record back.
    spot_check(
        collection,
        chunk_id=chunks[0]["id"]
    )

    print("\n" + "=" * 60)
    print("VECTOR DATABASE READY")
    print("=" * 60)


if __name__ == "__main__":
    main()
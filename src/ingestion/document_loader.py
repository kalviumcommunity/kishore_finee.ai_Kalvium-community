from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm"}


def load_text(path: Path) -> str:
    """
    Load a document and return its contents as plain text.
    Supports PDF, TXT, Markdown, and HTML.
    """
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix in {".html", ".htm"}:
        html = path.read_text(encoding="utf-8", errors="ignore")
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

    raise ValueError(f"Unsupported file type: {suffix}")


def load_documents(data_dir: Path) -> list[dict]:
    """
    Load supported documents recursively.

    Failed or unsupported files are skipped instead of
    stopping the entire ingestion process.
    """
    documents = []

    for path in data_dir.rglob("*"):
        if not path.is_file() or path.name == ".gitkeep":
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"SKIP {path.name}: unsupported file type")
            continue

        try:
            text = load_text(path)

            if not text.strip():
                print(f"SKIP {path.name}: no extractable text")
                continue

            document = {
                "source": path.name,
                "text": text,
            }

            documents.append(document)

            preview = " ".join(text.split())[:100]

            print(
                f"OK {path.name}: "
                f"{len(text)} chars | "
                f"Preview: {preview!r}"
            )

        except Exception as error:
            print(f"SKIP {path.name}: {error}")

    return documents


if __name__ == "__main__":
    data_dir = Path("data/sample")

    documents = load_documents(data_dir)

    print("\n" + "=" * 60)
    print(f"Documents loaded successfully: {len(documents)}")
    print("=" * 60)
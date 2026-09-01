import re
import unicodedata
from collections import defaultdict

def fix_mojibake(text: str) -> str:
    """
    Fix common UTF-8 Mojibake artifacts.
    """
    replacements = {
        "â€™": "’",
        "â€œ": "“",
        "â€\x9d": "”",
        "â€": "”",
        "â€“": "–",
        "â€”": "—",
        "â€¦": "…",
        "Â©": "©",
        "Â®": "®",
        "â„¢": "™",
        "Â": "",
    }
    # Sort by length descending to replace longer patterns first
    for bad, good in sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True):
        text = text.replace(bad, good)
    return text

def split_into_pages(text: str) -> list[str]:
    """
    Split text into pages based on form feeds and page markers.
    """
    # First, split by form feed
    if "\x0c" in text:
        initial_segments = text.split("\x0c")
    else:
        initial_segments = [text]

    PAGE_MARKER_REGEX = re.compile(
        r'(?:'
        r'\bPage\s+\d+\s+of\s+\d+\b'
        r'|^\s*Page\s+\d+\s*$'
        r'|^\s*-\s*\d+\s*-\s*$'
        r'|^\s*\[\s*\d+\s*\]\s*$'
        r')',
        re.MULTILINE | re.IGNORECASE
    )

    final_segments = []
    for seg in initial_segments:
        parts = PAGE_MARKER_REGEX.split(seg)
        final_segments.extend(parts)
    
    return final_segments

def detect_and_remove_headers_footers(
    segments: list[str],
    min_pages: int = 2,
    threshold: float = 0.5,
    max_header_lines: int = 2,
    max_footer_lines: int = 2,
) -> list[str]:
    """
    Detect and remove repeated page headers and footers across page segments.
    """
    if len(segments) < min_pages:
        return segments

    # Prepare lines for each segment
    segment_lines = []
    for seg in segments:
        # Split and strip trailing whitespace from each line
        lines = [line.rstrip() for line in seg.split("\n")]
        segment_lines.append(lines)

    top_counts = defaultdict(int)
    bottom_counts = defaultdict(int)

    # Count top and bottom candidate lines across pages
    for lines in segment_lines:
        top_candidates = []
        count = 0
        for line in lines:
            if line.strip():
                top_candidates.append(line.strip())
                count += 1
                if count >= max_header_lines:
                    break
        for cand in set(top_candidates):
            top_counts[cand] += 1

        bottom_candidates = []
        count = 0
        for line in reversed(lines):
            if line.strip():
                bottom_candidates.append(line.strip())
                count += 1
                if count >= max_footer_lines:
                    break
        for cand in set(bottom_candidates):
            bottom_counts[cand] += 1

    # Identify repeated headers and footers
    num_pages = len(segments)
    repeated_headers = {
        cand for cand, cnt in top_counts.items()
        if cnt >= min_pages and (cnt / num_pages) >= threshold
    }
    repeated_footers = {
        cand for cand, cnt in bottom_counts.items()
        if cnt >= min_pages and (cnt / num_pages) >= threshold
    }

    # Remove repeated headers and footers from each page
    cleaned_segments = []
    for lines in segment_lines:
        top_remove_indices = set()
        count = 0
        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            if line.strip() in repeated_headers:
                top_remove_indices.add(idx)
                count += 1
                if count >= max_header_lines:
                    pass
            else:
                break

        bottom_remove_indices = set()
        count = 0
        for idx in range(len(lines) - 1, -1, -1):
            if idx in top_remove_indices:
                break
            line = lines[idx]
            if not line.strip():
                continue
            if line.strip() in repeated_footers:
                bottom_remove_indices.add(idx)
                count += 1
                if count >= max_footer_lines:
                    pass
            else:
                break

        all_remove_indices = top_remove_indices.union(bottom_remove_indices)
        cleaned_lines = [
            line for idx, line in enumerate(lines)
            if idx not in all_remove_indices
        ]
        cleaned_segments.append("\n".join(cleaned_lines))

    return cleaned_segments

def clean_text(text: str) -> str:
    """
    Clean extracted document text using a conservative pipeline.
    """
    if not text:
        return ""

    # 1. Fix common UTF-8 Mojibake artifacts (must be done before NFKC to prevent character transformations)
    text = fix_mojibake(text)

    # 2. Unicode normalization using NFKC
    text = unicodedata.normalize("NFKC", text)

    # 3. Normalize line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Split into page segments based on form feeds and page markers
    segments = split_into_pages(text)

    # 5. Detect and remove repeated page headers and footers
    cleaned_segments = detect_and_remove_headers_footers(segments)

    # 6. Reassemble document
    text = "\n".join(cleaned_segments)

    # 7. Collapse repeated spaces and tabs on a per-line basis (keeping newlines intact)
    lines = text.split("\n")
    collapsed_lines = [re.sub(r"[ \t]+", " ", line) for line in lines]
    text = "\n".join(collapsed_lines)

    # 8. Collapse excessive blank lines (more than 2 consecutive newlines to exactly 2 newlines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 9. Strip unnecessary leading/trailing whitespace
    return text.strip()

def clean_documents(documents: list[dict], verbose: bool = True) -> list[dict]:
    """
    Process multiple extracted documents using exactly the same cleaning rules.
    Returns a new list of dicts with cleaned text.
    """
    cleaned_docs = []
    for doc in documents:
        cleaned_doc = doc.copy()
        before_text = doc.get("text", "")
        after_text = clean_text(before_text)
        cleaned_doc["text"] = after_text
        cleaned_docs.append(cleaned_doc)
        
        if verbose:
            source = doc.get("source", "unknown")
            print(f"{source}: {len(before_text)} -> {len(after_text)} characters")
            
    return cleaned_docs

from src.ingestion.text_cleaner import clean_text, clean_documents

def test_nfkc_unicode_normalization():
    # Full-width 'A' is '\uff21', which normalizes to standard ASCII 'A'.
    # Ligature 'ﬁ' (U+FB01) normalizes to 'fi'.
    # Mojibake example like "â€™" which should resolve to "’".
    text = "\uff21 ﬁ â€™ â€œ â€\x9d â€“ Â©"
    cleaned = clean_text(text)
    assert "A fi ’ “ ” – ©" in cleaned

def test_windows_line_endings():
    text = "Line 1\r\nLine 2\rLine 3\nLine 4"
    cleaned = clean_text(text)
    assert cleaned == "Line 1\nLine 2\nLine 3\nLine 4"

def test_page_footer_removal():
    text = "Some content.\nPage 3 of 12\nSome other content."
    cleaned = clean_text(text)
    assert "Page 3 of 12" not in cleaned
    assert "Some content." in cleaned
    assert "Some other content." in cleaned

def test_excessive_spaces():
    text = "This    is   some   spaced    text."
    cleaned = clean_text(text)
    assert cleaned == "This is some spaced text."

def test_excessive_blank_lines():
    text = "Paragraph 1\n\n\n\nParagraph 2\n\n\nParagraph 3"
    cleaned = clean_text(text)
    assert cleaned == "Paragraph 1\n\nParagraph 2\n\nParagraph 3"

def test_leading_trailing_whitespace():
    text = "   \n\n  Leading and trailing.   \n\n  "
    cleaned = clean_text(text)
    assert cleaned == "Leading and trailing."

def test_repeated_header_footer_detection():
    text = (
        "Page 1 of 12\n"
        "Financial Advisory Report\n"
        "Marcus Johnson paid the advisory fee on 20 August.\n"
        "Page 2 of 12\n"
        "Financial Advisory Report\n"
        "The payment was completed.\n"
    )
    cleaned = clean_text(text)
    assert "Financial Advisory Report" not in cleaned
    assert "Marcus Johnson paid the advisory fee on 20 August." in cleaned
    assert "The payment was completed." in cleaned

def test_preservation_of_meaningful_numbers():
    text = "The code is 9988-A and the version is 2.3.4."
    cleaned = clean_text(text)
    assert cleaned == "The code is 9988-A and the version is 2.3.4."

def test_preservation_of_dates():
    text = "The payment was completed on 20 August 2026."
    cleaned = clean_text(text)
    assert cleaned == "The payment was completed on 20 August 2026."

def test_preservation_of_financial_amounts():
    text = "The amount is $1,250.50 or €900.00."
    cleaned = clean_text(text)
    assert cleaned == "The amount is $1,250.50 or €900.00."

def test_preservation_of_headings():
    text = "# Section 1: Financial Overview\n\nHere is the overview."
    cleaned = clean_text(text)
    assert cleaned == "# Section 1: Financial Overview\n\nHere is the overview."

def test_empty_input():
    assert clean_text("") == ""
    assert clean_text(None) == ""

def test_already_clean_input():
    text = "This is clean text.\n\nIt has standard paragraphs."
    assert clean_text(text) == text

def test_multiple_documents():
    docs = [
        {
            "source": "doc1.txt",
            "text": "Page 1 of 12\nFinancial Advisory Report\nFirst document page 1.\nPage 2 of 12\nFinancial Advisory Report\nFirst document page 2."
        },
        {
            "source": "doc2.txt",
            "text": "Page 1 of 12\nFinancial Advisory Report\nSecond document page 1.\nPage 2 of 12\nFinancial Advisory Report\nSecond document page 2."
        }
    ]
    cleaned = clean_documents(docs, verbose=True)
    # Check that original is not modified
    assert docs[0]["text"].startswith("Page 1 of 12")
    # Check that cleaned docs are cleaned consistently
    assert "Financial Advisory Report" not in cleaned[0]["text"]
    assert "Financial Advisory Report" not in cleaned[1]["text"]
    assert "First document page 1." in cleaned[0]["text"]
    assert "Second document page 1." in cleaned[1]["text"]


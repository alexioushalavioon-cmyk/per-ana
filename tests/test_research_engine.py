from app.services.research import canonicalize_url, content_hash, extract_sentence_evidence


def test_canonicalize_url_removes_tracking() -> None:
    assert canonicalize_url("HTTPS://Example.COM/a/?utm_source=x&b=2#frag") == "https://example.com/a?b=2"


def test_content_hash_is_whitespace_stable() -> None:
    assert content_hash("A   policy\nclaim") == content_hash("a policy claim")


def test_extract_sentence_evidence_filters_short_fragments() -> None:
    text = "کوتاه. این یک گزاره نسبتاً کامل درباره یک سیاست عمومی است که باید به عنوان شاهد استخراج شود."
    claims = extract_sentence_evidence(text, max_claims=5)
    assert len(claims) == 1
    assert "سیاست عمومی" in claims[0]

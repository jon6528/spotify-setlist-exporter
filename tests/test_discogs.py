from app.discogs import _normalize


def test_normalize_lowercases():
    assert _normalize("Gloria") == "gloria"


def test_normalize_strips_punctuation():
    assert _normalize("Rock 'n' Roll") == "rock n roll"


def test_normalize_collapses_whitespace():
    assert _normalize("  Hello   World  ") == "hello world"


def test_normalize_handles_empty():
    assert _normalize("") == ""

from app.discogs import _normalize


def test_normalize_lowercases():
    assert _normalize("Gloria") == "gloria"


def test_normalize_strips_punctuation():
    assert _normalize("Rock 'n' Roll") == "rock n roll"


def test_normalize_collapses_whitespace():
    assert _normalize("  Hello   World  ") == "hello world"


def test_normalize_handles_empty():
    assert _normalize("") == ""


def test_normalize_strips_parenthetical_suffix():
    assert _normalize("Heroes (2017 Remaster)") == "heroes 2017 remaster"


def test_normalize_strips_accented_characters():
    assert _normalize("café") == "cafe"


def test_normalize_strips_underscores():
    assert _normalize("Side_A") == "side a"


from unittest.mock import patch, Mock
from app.discogs import _lookup_vinyl_positions


def test_lookup_returns_empty_without_token(monkeypatch):
    monkeypatch.delenv("DISCOGS_TOKEN", raising=False)
    assert _lookup_vinyl_positions("Patti Smith", "Horses") == {}


def test_lookup_returns_position_map(monkeypatch):
    monkeypatch.setenv("DISCOGS_TOKEN", "tok")
    search_mock = Mock(ok=True)
    search_mock.json.return_value = {"results": [{"id": 123}]}
    release_mock = Mock(ok=True)
    release_mock.json.return_value = {
        "tracklist": [
            {"title": "Gloria", "position": "A1"},
            {"title": "Birdland", "position": "A3"},
            {"title": "Free Money", "position": "B1"},
        ]
    }
    with patch("app.discogs.requests.get", side_effect=[search_mock, release_mock]):
        result = _lookup_vinyl_positions("Patti Smith", "Horses")
    assert result == {"gloria": "A1", "birdland": "A3", "free money": "B1"}


def test_lookup_returns_empty_on_no_search_results(monkeypatch):
    monkeypatch.setenv("DISCOGS_TOKEN", "tok")
    mock = Mock(ok=True)
    mock.json.return_value = {"results": []}
    with patch("app.discogs.requests.get", return_value=mock):
        assert _lookup_vinyl_positions("Unknown", "Album") == {}


def test_lookup_returns_empty_on_api_error(monkeypatch):
    monkeypatch.setenv("DISCOGS_TOKEN", "tok")
    mock = Mock(ok=False)
    with patch("app.discogs.requests.get", return_value=mock):
        assert _lookup_vinyl_positions("Patti Smith", "Horses") == {}


def test_lookup_returns_empty_on_network_error(monkeypatch):
    monkeypatch.setenv("DISCOGS_TOKEN", "tok")
    with patch("app.discogs.requests.get", side_effect=Exception("timeout")):
        assert _lookup_vinyl_positions("Patti Smith", "Horses") == {}

from unittest.mock import patch, Mock
from app.discogs import _normalize, _lookup_vinyl_positions, enrich_tracks


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


def test_lookup_returns_empty_on_release_fetch_error(monkeypatch):
    monkeypatch.setenv("DISCOGS_TOKEN", "tok")
    search_mock = Mock(ok=True)
    search_mock.json.return_value = {"results": [{"id": 123}]}
    release_mock = Mock(ok=False)
    with patch("app.discogs.requests.get", side_effect=[search_mock, release_mock]):
        assert _lookup_vinyl_positions("Patti Smith", "Horses") == {}


def test_lookup_returns_empty_on_network_error(monkeypatch):
    monkeypatch.setenv("DISCOGS_TOKEN", "tok")
    with patch("app.discogs.requests.get", side_effect=Exception("timeout")):
        assert _lookup_vinyl_positions("Patti Smith", "Horses") == {}


def test_enrich_adds_side_when_match_found():
    tracks = [{"name": "Gloria", "artist": "Patti Smith", "album": "Horses",
               "track_number": 1, "duration": "5:55"}]
    with patch("app.discogs._lookup_vinyl_positions", return_value={"gloria": "A1"}):
        enrich_tracks(tracks)
    assert tracks[0]["side"] == "A1"


def test_enrich_sets_none_when_no_match():
    tracks = [{"name": "Unknown Track", "artist": "X", "album": "Y",
               "track_number": 1, "duration": "3:00"}]
    with patch("app.discogs._lookup_vinyl_positions", return_value={}):
        enrich_tracks(tracks)
    assert tracks[0]["side"] is None


def test_enrich_deduplicates_api_calls():
    tracks = [
        {"name": "Gloria", "artist": "Patti Smith", "album": "Horses",
         "track_number": 1, "duration": "5:55"},
        {"name": "Birdland", "artist": "Patti Smith", "album": "Horses",
         "track_number": 3, "duration": "9:14"},
    ]
    with patch("app.discogs._lookup_vinyl_positions", return_value={}) as mock_lookup:
        enrich_tracks(tracks)
    mock_lookup.assert_called_once_with("Patti Smith", "Horses")


def test_enrich_handles_multiple_albums():
    tracks = [
        {"name": "Gloria", "artist": "Patti Smith", "album": "Horses",
         "track_number": 1, "duration": "5:55"},
        {"name": "Heroes", "artist": "David Bowie", "album": "Heroes",
         "track_number": 1, "duration": "6:07"},
    ]
    with patch("app.discogs._lookup_vinyl_positions", return_value={}) as mock_lookup:
        enrich_tracks(tracks)
    assert mock_lookup.call_count == 2

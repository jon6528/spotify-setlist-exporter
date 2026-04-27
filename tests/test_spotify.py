import pytest
from unittest.mock import patch, Mock
from app.spotify import parse_playlist_id


def test_parse_standard_url():
    assert parse_playlist_id(
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    ) == "37i9dQZF1DXcBWIGoYBM5M"


def test_parse_url_with_query_params():
    assert parse_playlist_id(
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc123"
    ) == "37i9dQZF1DXcBWIGoYBM5M"


def test_parse_invalid_url_raises():
    with pytest.raises(ValueError, match="Invalid Spotify playlist URL"):
        parse_playlist_id("https://open.spotify.com/track/123")


def test_parse_empty_raises():
    with pytest.raises(ValueError, match="Invalid Spotify playlist URL"):
        parse_playlist_id("")


# Task 3: get_auth_url
from urllib.parse import parse_qs, urlparse as _urlparse


def test_get_auth_url_contains_required_params(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test_cid")
    from app.spotify import get_auth_url
    url = get_auth_url(redirect_uri="http://localhost:8000/callback")
    parsed = _urlparse(url)
    params = parse_qs(parsed.query)
    assert parsed.netloc == "accounts.spotify.com"
    assert params["client_id"] == ["test_cid"]
    assert params["response_type"] == ["code"]
    assert params["redirect_uri"] == ["http://localhost:8000/callback"]
    assert "playlist-read-private" in params["scope"][0]
    assert "playlist-read-collaborative" in params["scope"][0]


# Task 4: exchange_code
def test_exchange_code_returns_access_token(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "cid")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "csecret")
    mock_resp = Mock()
    mock_resp.json.return_value = {"access_token": "tok123"}
    mock_resp.raise_for_status = Mock()
    with patch("app.spotify.requests.post", return_value=mock_resp) as mock_post:
        from app.spotify import exchange_code
        token = exchange_code(code="authcode", redirect_uri="http://localhost:8000/callback")
    assert token == "tok123"
    posted_data = mock_post.call_args[1]["data"]
    assert posted_data["grant_type"] == "authorization_code"
    assert posted_data["code"] == "authcode"


def test_exchange_code_raises_on_http_error(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "cid")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "csecret")
    mock_resp = Mock()
    mock_resp.raise_for_status.side_effect = Exception("401 Unauthorized")
    with patch("app.spotify.requests.post", return_value=mock_resp):
        from app.spotify import exchange_code
        with pytest.raises(Exception):
            exchange_code(code="bad", redirect_uri="http://localhost:8000/callback")


# Task 5: get_playlist_tracks
def _make_item(name, artist, album, track_number, duration_ms):
    return {
        "track": {
            "name": name,
            "track_number": track_number,
            "duration_ms": duration_ms,
            "artists": [{"name": artist}],
            "album": {"name": album},
        }
    }


def test_get_playlist_tracks_single_page():
    playlist_data = {
        "name": "My Playlist",
        "tracks": {
            "items": [_make_item("Song A", "Artist A", "Album A", 3, 200000)],
            "next": None,
        },
    }
    mock_resp = Mock(status_code=200)
    mock_resp.json.return_value = playlist_data
    with patch("app.spotify.requests.get", return_value=mock_resp):
        from app.spotify import get_playlist_tracks
        name, tracks = get_playlist_tracks(token="tok", playlist_id="abc")
    assert name == "My Playlist"
    assert tracks == [{
        "track_number": 3,
        "name": "Song A",
        "artist": "Artist A",
        "album": "Album A",
        "duration": "3:20",
    }]


def test_get_playlist_tracks_paginates():
    page1 = {
        "name": "Big Playlist",
        "tracks": {
            "items": [_make_item("Song A", "Artist A", "Album A", 1, 60000)],
            "next": "https://api.spotify.com/v1/playlists/abc/tracks?offset=100",
        },
    }
    page2 = {
        "items": [_make_item("Song B", "Artist B", "Album B", 2, 120000)],
        "next": None,
    }
    mock1 = Mock(status_code=200)
    mock1.json.return_value = page1
    mock2 = Mock(status_code=200)
    mock2.json.return_value = page2
    with patch("app.spotify.requests.get", side_effect=[mock1, mock2]):
        from app.spotify import get_playlist_tracks
        name, tracks = get_playlist_tracks(token="tok", playlist_id="abc")
    assert len(tracks) == 2
    assert tracks[1]["name"] == "Song B"


def test_get_playlist_tracks_raises_auth_error_on_401():
    mock_resp = Mock(status_code=401)
    with patch("app.spotify.requests.get", return_value=mock_resp):
        from app.spotify import get_playlist_tracks, SpotifyAuthError
        with pytest.raises(SpotifyAuthError):
            get_playlist_tracks(token="expired", playlist_id="abc")

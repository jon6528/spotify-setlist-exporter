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

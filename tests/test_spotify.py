import pytest
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

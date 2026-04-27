import os
import base64
import requests
from urllib.parse import urlparse, urlencode


def parse_playlist_id(url: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "playlist":
        return parts[1]
    raise ValueError("Invalid Spotify playlist URL")


SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SCOPES = "playlist-read-private playlist-read-collaborative"


def get_auth_url(redirect_uri: str) -> str:
    params = {
        "client_id": os.environ["SPOTIFY_CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"

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


SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


def exchange_code(code: str, redirect_uri: str) -> str:
    client_id = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {credentials}"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


SPOTIFY_API_BASE = "https://api.spotify.com/v1"


class SpotifyAuthError(Exception):
    pass


def _ms_to_duration(ms: int) -> str:
    seconds = ms // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


def get_playlist_tracks(token: str, playlist_id: str) -> tuple[str, list[dict]]:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{SPOTIFY_API_BASE}/playlists/{playlist_id}", headers=headers)
    if response.status_code == 401:
        raise SpotifyAuthError("Spotify token expired or invalid")
    if not response.ok:
        raise ValueError(f"Could not load playlist (Spotify returned {response.status_code})")
    data = response.json()
    playlist_name = data["name"]
    tracks = []
    page = data["tracks"]
    while page:
        for item in page.get("items", []):
            t = item.get("track")
            if not t:
                continue
            tracks.append({
                "track_number": t["track_number"],
                "name": t["name"],
                "artist": t["artists"][0]["name"],
                "album": t["album"]["name"],
                "duration": _ms_to_duration(t["duration_ms"]),
            })
        next_url = page.get("next")
        if next_url:
            response = requests.get(next_url, headers=headers)
            if response.status_code == 401:
                raise SpotifyAuthError("Spotify token expired or invalid")
            if not response.ok:
                raise ValueError(f"Could not load playlist page (Spotify returned {response.status_code})")
            page = response.json()
        else:
            page = None
    return playlist_name, tracks

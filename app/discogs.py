import os
import re
import unicodedata
import requests

DISCOGS_API_BASE = "https://api.discogs.com"
_HEADERS = {"User-Agent": "SpotifySetlistExporter/1.0"}


def _normalize(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    name = name.replace("_", " ")
    name = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _lookup_vinyl_positions(artist: str, album: str) -> dict[str, str]:
    token = os.environ.get("DISCOGS_TOKEN")
    if not token:
        return {}
    try:
        search_resp = requests.get(
            f"{DISCOGS_API_BASE}/database/search",
            params={
                "artist": artist,
                "release_title": album,
                "format": "vinyl",
                "token": token,
            },
            headers=_HEADERS,
            timeout=10,
        )
        if not search_resp.ok:
            return {}
        results = search_resp.json().get("results", [])
        if not results:
            return {}
        release_id = results[0]["id"]
        release_resp = requests.get(
            f"{DISCOGS_API_BASE}/releases/{release_id}",
            params={"token": token},
            headers=_HEADERS,
            timeout=10,
        )
        if not release_resp.ok:
            return {}
        tracklist = release_resp.json().get("tracklist", [])
        return {
            _normalize(t["title"]): t.get("position", "")
            for t in tracklist
            if t.get("title") and t.get("position")
        }
    except Exception:
        return {}


def enrich_tracks(tracks: list[dict]) -> None:
    cache: dict[tuple[str, str], dict[str, str]] = {}
    for track in tracks:
        key = (track["artist"], track["album"])
        if key not in cache:
            cache[key] = _lookup_vinyl_positions(track["artist"], track["album"])
        track["side"] = cache[key].get(_normalize(track["name"]))

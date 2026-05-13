import os
import re
import unicodedata
import requests

DISCOGS_API_BASE = "https://api.discogs.com"
_HEADERS = {"User-Agent": "SpotifySetlistExporter/1.0"}


def _normalize(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    name = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

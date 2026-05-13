import os
import re
import requests

DISCOGS_API_BASE = "https://api.discogs.com"
_HEADERS = {"User-Agent": "SpotifySetlistExporter/1.0"}


def _normalize(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

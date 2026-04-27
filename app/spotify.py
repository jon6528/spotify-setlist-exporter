from urllib.parse import urlparse


def parse_playlist_id(url: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "playlist":
        return parts[1]
    raise ValueError("Invalid Spotify playlist URL")

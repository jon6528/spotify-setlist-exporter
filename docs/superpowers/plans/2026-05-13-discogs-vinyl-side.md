# Discogs Vinyl Side Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich playlist tracks with vinyl side position from Discogs so users can quickly locate tracks on a record during live performance.

**Architecture:** A new `app/discogs.py` module handles all Discogs API logic. The `/playlist` and `/export` routes call `discogs.enrich_tracks()` after fetching Spotify data, mutating each track dict with a `side` field. Side is rendered as the first column in both the UI table and the CSV export.

**Tech Stack:** Python requests (already in requirements.txt), Discogs REST API, existing FastAPI/Jinja2 stack.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `app/discogs.py` | Create | All Discogs API logic: normalize, lookup, enrich |
| `tests/test_discogs.py` | Create | Full unit test coverage for discogs module |
| `app/main.py` | Modify | Call enrich_tracks in /playlist and /export; update CSV |
| `app/templates/playlist.html` | Modify | Add Side as first column |
| `docker-compose.yml` | Modify | Add DISCOGS_TOKEN to environment block |
| `.env.example` | Modify | Add DISCOGS_TOKEN |
| `tests/test_routes.py` | Modify | Update CSV header assertion to include Side |

---

## Task 1: Add DISCOGS_TOKEN to config files

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`

- [ ] **Step 1: Update docker-compose.yml**

Replace the environment block so it reads:

```yaml
services:
  web:
    build: .
    ports:
      - "8080:8000"
    environment:
      - SECRET_KEY=
      - SPOTIFY_CLIENT_ID=
      - SPOTIFY_CLIENT_SECRET=
      - REDIRECT_URI=
      - DISCOGS_TOKEN=
```

- [ ] **Step 2: Update .env.example**

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=replace_with_any_long_random_string
REDIRECT_URI=http://localhost:8080/callback
DISCOGS_TOKEN=your_discogs_token_here
```

To get a Discogs token: log in at discogs.com → Settings → Developers → Generate Token.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "config: add DISCOGS_TOKEN environment variable"
```

---

## Task 2: Create app/discogs.py with _normalize

**Files:**
- Create: `app/discogs.py`
- Create: `tests/test_discogs.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_discogs.py`:

```python
from app.discogs import _normalize


def test_normalize_lowercases():
    assert _normalize("Gloria") == "gloria"


def test_normalize_strips_punctuation():
    assert _normalize("Rock 'n' Roll") == "rock n roll"


def test_normalize_collapses_whitespace():
    assert _normalize("  Hello   World  ") == "hello world"


def test_normalize_handles_empty():
    assert _normalize("") == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_discogs.py -v
```

Expected: `ImportError` — module does not exist yet.

- [ ] **Step 3: Create app/discogs.py with _normalize**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_discogs.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add app/discogs.py tests/test_discogs.py
git commit -m "feat: add discogs module with name normalization"
```

---

## Task 3: Implement _lookup_vinyl_positions

**Files:**
- Modify: `app/discogs.py` (add function)
- Modify: `tests/test_discogs.py` (add tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_discogs.py`:

```python
from unittest.mock import patch, Mock
from app.discogs import _lookup_vinyl_positions


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


def test_lookup_returns_empty_on_network_error(monkeypatch):
    monkeypatch.setenv("DISCOGS_TOKEN", "tok")
    with patch("app.discogs.requests.get", side_effect=Exception("timeout")):
        assert _lookup_vinyl_positions("Patti Smith", "Horses") == {}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_discogs.py::test_lookup_returns_empty_without_token -v
```

Expected: `ImportError` — function not defined yet.

- [ ] **Step 3: Add _lookup_vinyl_positions to app/discogs.py**

Append after `_normalize`:

```python
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
```

- [ ] **Step 4: Run all discogs tests to verify they pass**

```bash
python3 -m pytest tests/test_discogs.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add app/discogs.py tests/test_discogs.py
git commit -m "feat: add Discogs vinyl position lookup"
```

---

## Task 4: Implement enrich_tracks

**Files:**
- Modify: `app/discogs.py` (add function)
- Modify: `tests/test_discogs.py` (add tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_discogs.py`:

```python
from app.discogs import enrich_tracks


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_discogs.py::test_enrich_adds_side_when_match_found -v
```

Expected: `ImportError` — function not defined yet.

- [ ] **Step 3: Add enrich_tracks to app/discogs.py**

Append after `_lookup_vinyl_positions`:

```python
def enrich_tracks(tracks: list[dict]) -> None:
    cache: dict[tuple[str, str], dict[str, str]] = {}
    for track in tracks:
        key = (track["artist"], track["album"])
        if key not in cache:
            cache[key] = _lookup_vinyl_positions(track["artist"], track["album"])
        track["side"] = cache[key].get(_normalize(track["name"]))
```

- [ ] **Step 4: Run all discogs tests to verify they pass**

```bash
python3 -m pytest tests/test_discogs.py -v
```

Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add app/discogs.py tests/test_discogs.py
git commit -m "feat: add enrich_tracks with per-album deduplication"
```

---

## Task 5: Integrate Discogs into routes and update CSV

**Files:**
- Modify: `app/main.py`
- Modify: `tests/test_routes.py` (fix broken CSV header assertion)

- [ ] **Step 1: Update app/main.py**

Add the import after the existing `from app import spotify` line:

```python
from app import spotify, discogs
```

In the `load_playlist` route, add `discogs.enrich_tracks(tracks)` after `get_playlist_tracks`:

```python
@app.post("/playlist", response_class=HTMLResponse)
def load_playlist(request: Request, playlist_url: str = Form(...)):
    token = request.session.get("access_token")
    if not token:
        return RedirectResponse("/", status_code=303)
    try:
        playlist_id = spotify.parse_playlist_id(playlist_url)
        playlist_name, tracks = spotify.get_playlist_tracks(token=token, playlist_id=playlist_id)
        discogs.enrich_tracks(tracks)
        request.session["playlist_id"] = playlist_id
        request.session["playlist_name"] = playlist_name
    except spotify.SpotifyAuthError:
        request.session.clear()
        return RedirectResponse("/", status_code=303)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "home.html",
            {"logged_in": True, "error": str(e)},
        )
    return templates.TemplateResponse(
        request,
        "playlist.html",
        {
            "playlist_name": playlist_name,
            "track_count": len(tracks),
            "tracks": tracks,
        },
    )
```

In the `export_csv` route, add `discogs.enrich_tracks(tracks)` after `get_playlist_tracks`, and update the CSV writer:

```python
@app.get("/export")
def export_csv(request: Request):
    token = request.session.get("access_token")
    playlist_id = request.session.get("playlist_id")
    playlist_name = request.session.get("playlist_name", "playlist")
    if not token or not playlist_id:
        return RedirectResponse("/")
    try:
        _, tracks = spotify.get_playlist_tracks(token=token, playlist_id=playlist_id)
    except spotify.SpotifyAuthError:
        request.session.clear()
        return RedirectResponse("/")
    except ValueError:
        return RedirectResponse("/")
    discogs.enrich_tracks(tracks)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Side", "Track Number", "Track Name", "Artist", "Album", "Track Length"])
    for t in tracks:
        writer.writerow([
            t.get("side") or "",
            t["track_number"],
            t["name"],
            t["artist"],
            t["album"],
            t["duration"],
        ])
    filename = re.sub(r"[^\w\s-]", "", playlist_name).strip().lower()
    filename = re.sub(r"\s+", "-", filename)
    filename = filename or "playlist"
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )
```

- [ ] **Step 2: Run existing route tests and identify the one that breaks**

```bash
python3 -m pytest tests/test_routes.py -v
```

Expected: `test_export_returns_csv` fails — the CSV header assertion references the old header string.

- [ ] **Step 3: Fix the broken test in tests/test_routes.py**

Find line 136 in `tests/test_routes.py`:

```python
assert "Track Number,Track Name,Artist,Album,Track Length" in resp.text
```

Change it to:

```python
assert "Side,Track Number,Track Name,Artist,Album,Track Length" in resp.text
```

- [ ] **Step 4: Run all tests to verify everything passes**

```bash
python3 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/test_routes.py
git commit -m "feat: enrich tracks with Discogs side data in playlist and export routes"
```

---

## Task 6: Add Side column to playlist.html

**Files:**
- Modify: `app/templates/playlist.html`

- [ ] **Step 1: Update playlist.html**

Replace the full file with:

```html
{% extends "base.html" %}

{% block nav_extra %}
<form class="url-form" method="post" action="/playlist">
  <input class="url-input" type="text" name="playlist_url"
    placeholder="https://open.spotify.com/playlist/...">
  <button class="btn btn-sm" type="submit">Load</button>
</form>
{% endblock %}

{% block content %}
<div class="playlist-header">
  <h2>{{ playlist_name }}</h2>
  <p>{{ track_count }} tracks</p>
</div>
<table class="track-table">
  <thead>
    <tr>
      <th class="track-side">Side</th>
      <th class="track-num">#</th>
      <th>Title</th>
      <th>Artist</th>
      <th>Album</th>
      <th class="track-duration">&#9201;</th>
    </tr>
  </thead>
  <tbody>
  {% for t in tracks %}
  <tr>
    <td class="track-side">{{ t.side or '' }}</td>
    <td class="track-num">{{ t.track_number }}</td>
    <td class="track-name">{{ t.name }}</td>
    <td class="track-artist">{{ t.artist }}</td>
    <td class="track-album">{{ t.album }}</td>
    <td class="track-duration">{{ t.duration }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
<div class="export-bar">
  <a href="/export" class="btn">&#11015; Export CSV</a>
</div>
{% endblock %}
```

- [ ] **Step 2: Run full test suite to confirm nothing broke**

```bash
python3 -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit and push**

```bash
git add app/templates/playlist.html
git commit -m "feat: add Side column as first column in playlist table"
git push
```

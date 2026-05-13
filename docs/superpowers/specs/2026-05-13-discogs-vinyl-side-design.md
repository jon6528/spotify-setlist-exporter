# Discogs Vinyl Side Enrichment — Design Spec

**Date:** 2026-05-13
**Status:** Approved

---

## Overview

Enrich playlist tracks with vinyl side position data from Discogs so users can quickly locate tracks on a record during a live performance without reading album covers.

---

## Architecture & Data Flow

A new `app/discogs.py` module handles all Discogs API logic in isolation. The `/playlist` route in `main.py` calls it after fetching Spotify tracks.

```
POST /playlist
  → spotify.get_playlist_tracks()     # existing, unchanged
  → discogs.enrich_tracks(tracks)     # new — adds side field per track
  → render playlist.html              # shows enriched data including side
```

`enrich_tracks()` groups tracks by `(artist, album)`, performs one Discogs search + release fetch per unique album, then fills in `side` on each track dict. Tracks with no Discogs match get `side = None`.

If `DISCOGS_TOKEN` is not set in the environment, enrichment is skipped entirely and all `side` values are `None`.

---

## Discogs Module (`app/discogs.py`)

### `enrich_tracks(tracks: list[dict]) -> None`

Mutates the track list in place, adding a `side` key to each dict.

Steps:
1. Group tracks by `(artist, album)` to deduplicate API calls
2. For each unique album, call `_lookup_vinyl_positions(artist, album)`
3. For each track, match by name to the returned position map and set `side`

### `_lookup_vinyl_positions(artist, album) -> dict[str, str]`

Returns a mapping of `track_name_normalized → position` (e.g. `"birdland" → "A3"`).

Steps:
1. Search: `GET /database/search?artist={artist}&release_title={album}&format=vinyl&token={token}`
2. Take the first result — if none, return empty dict
3. Fetch: `GET /releases/{release_id}`
4. Parse each tracklist entry: extract position and normalize name
5. Return the name→position map

### Position parsing

`"A1"` → `"A1"`, `"B12"` → `"B12"`, `"C3"` → `"C3"`

Non-standard positions (numeric only, e.g. `"1"`, `"2"`) are stored as-is and displayed as-is.

### Name normalization for matching

Lowercase, strip punctuation, collapse whitespace. Applied to both Discogs tracklist names and Spotify track names before comparison.

---

## API Details

- Base URL: `https://api.discogs.com`
- Auth: `?token={DISCOGS_TOKEN}` query parameter
- User-Agent header required: `SpotifySetlistExporter/1.0`
- Rate limit: 60 requests/minute (authenticated) — well within range for typical playlist sizes
- Errors (non-200, network failures): log and return empty dict; do not crash

---

## Column Layout

### CSV export

| Side | Track Number | Track Name | Artist | Album | Track Length |
|---|---|---|---|---|---|
| A1 | 1 | Gloria | Patti Smith | Horses | 5:55 |
| A3 | 3 | Birdland | Patti Smith | Horses | 9:14 |
| B1 | 4 | Free Money | Patti Smith | Horses | 3:23 |
|  | 3 | Song Title | Artist | Album | 3:30 |

- **Side** is the first column — full Discogs position (`A1`, `B3`, etc.), blank if no match
- **Track Number** remains the Spotify album-wide track number

### Track table (playlist.html)

Same column order as CSV. Side column added as the first column. Blank cell when no match.

---

## Environment Variable

| Variable | Purpose |
|---|---|
| `DISCOGS_TOKEN` | Discogs personal access token. If absent, Side column is blank for all tracks. |

Added to:
- `docker-compose.yml` environment block
- `.env.example`

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| `DISCOGS_TOKEN` not set | Skip enrichment, all Side values blank |
| Discogs search returns no vinyl results | Side blank for all tracks on that album |
| Discogs API returns non-200 | Log warning, Side blank for that album |
| Network error reaching Discogs | Log warning, Side blank for that album |
| Track name doesn't match any Discogs entry | Side blank for that track only |

All errors are non-fatal. The playlist and export always succeed; Side is simply omitted when unavailable.

---

## Testing

- `test_discogs.py` — unit tests with mocked HTTP:
  - Position parsing (`A1` → `"A1"`, `B12` → `"B12"`)
  - Name normalization and matching (punctuation, case)
  - Successful enrichment — side values populated correctly
  - No match from search — side stays None
  - API error — side stays None, no exception raised
  - Deduplication — only one API call per unique album even with multiple tracks from same album
  - Missing `DISCOGS_TOKEN` — enrichment skipped entirely

---

## Files Changed

| File | Change |
|---|---|
| `app/discogs.py` | New — all Discogs logic |
| `app/main.py` | Call `discogs.enrich_tracks()` in `/playlist` route; update CSV headers and row order |
| `app/templates/playlist.html` | Add Side as first column |
| `docker-compose.yml` | Add `DISCOGS_TOKEN=` to environment block |
| `.env.example` | Add `DISCOGS_TOKEN=` |
| `tests/test_discogs.py` | New — full test coverage for discogs module |

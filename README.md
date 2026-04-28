# Spotify Setlist Exporter

Paste a Spotify playlist link, preview all tracks, and download them as a CSV.

## Setup

### 1. Create a Spotify Developer App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Give it any name and description
4. Set **Redirect URI** to: `http://localhost:8000/callback`
5. Save — copy your **Client ID** and **Client Secret**

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SECRET_KEY=any_long_random_string
REDIRECT_URI=http://localhost:8000/callback
```

### 3. Run with Docker

```bash
docker-compose up
```

Open [http://localhost:8000](http://localhost:8000)

## Usage

1. Click **Login with Spotify** and authorize the app
2. Paste any Spotify playlist URL and click **Load**
3. Review the tracks in the table
4. Click **Export CSV** to download

## CSV Format

| Column | Description |
|---|---|
| Track Number | The song's position on its album |
| Track Name | Song title |
| Artist | First listed artist |
| Album | Album name |
| Track Length | Duration in m:ss |

## Development (without Docker)

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in .env
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest tests/ -v
```

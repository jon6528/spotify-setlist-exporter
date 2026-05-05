# Spotify Setlist Exporter

Paste a Spotify playlist link, preview all tracks, and download them as a CSV.

---

## NAS Setup (Synology, QNAP, Unraid, Portainer, etc.)

Running on a NAS means the app is always available on your local network — no need to keep a laptop open.

### 1. Find your NAS IP address

Look in your router's admin page or your NAS's network settings. It will be something like `192.168.1.100`. The app will be reachable at `http://192.168.1.100:8000`.

### 2. Create a Spotify Developer App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Give it any name and description
4. Set **Redirect URI** to: `http://192.168.1.100:8080/callback` (use your actual NAS IP)
5. Save — copy your **Client ID** and **Client Secret**

### 3. Build the Docker image on your NAS

SSH into your NAS, clone the repo, and build the image:

```bash
git clone https://github.com/jon6528/spotify-setlist-exporter.git
cd spotify-setlist-exporter
docker build -t spotify-setlist-exporter .
```

> If your NAS doesn't have `git`, download the repo as a ZIP from GitHub and extract it to the NAS via file browser, then run `docker build` from that folder.

### 4. Create the container in your Docker management UI

In your NAS container manager (Container Manager, Container Station, Portainer, etc.):

1. **Image:** `spotify-setlist-exporter` (the one you just built)
2. **Port mapping:** host port `8080` → container port `8000`
3. **Environment variables — add all four:**

| Variable | Value |
|---|---|
| `SPOTIFY_CLIENT_ID` | your Client ID from Step 2 |
| `SPOTIFY_CLIENT_SECRET` | your Client Secret from Step 2 |
| `SECRET_KEY` | any long random string (e.g. 40+ random characters) |
| `REDIRECT_URI` | `http://192.168.1.100:8080/callback` (your NAS IP) |

4. Start the container.

### 5. Open the app

Go to `http://192.168.1.100:8080` in your browser (use your actual NAS IP).

> **Tip:** Bookmark the NAS IP address URL — anyone on your local network can use it from any device.

---

## Local Setup (run on your computer)

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

---

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

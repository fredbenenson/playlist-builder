# Scripts

## build_playlist.py
Self-contained Spotify playlist builder. No external dependencies.

### Usage
```bash
# Create a new playlist
python3 build_playlist.py --name "Name" --description "..." --input tracks.json

# Add tracks to an existing playlist (for 502 recovery)
python3 build_playlist.py --name "ignored" --playlist-id "SPOTIFY_ID" --input missing.json
```

### Flags
- `--name` (required) -- Playlist name (ignored when `--playlist-id` is set)
- `--description` -- Playlist description
- `--input` (required) -- Path to JSON input file
- `--playlist-id` -- Add to existing playlist instead of creating new one

### Input Format (tracks.json)
```json
[
  {"artist": "Artist", "album": "Album", "track": "Track Name"},
  {"artist": "Artist", "album": "Album"}
]
```
- `track` is optional; if omitted, picks first track from the matched album

### Output
JSON to stdout with `playlist_url`, `tracks`, `not_found`. Progress logged to stderr.

### Retry Behavior
- Retries 429/500/502/503 errors up to 3 times with exponential backoff (2s/4s/6s)
- 0.5s delay between requests to avoid 502 cascades
- If many tracks still fail, re-run with `--playlist-id` and a JSON of just the missing tracks

### API Endpoints Used
- `POST /api/token` -- refresh token exchange
- `GET /search` -- track and album search (limit 10)
- `GET /albums/{id}/tracks` -- album track listing
- `POST /me/playlists` -- create playlist
- `POST /playlists/{id}/items` -- add tracks to playlist

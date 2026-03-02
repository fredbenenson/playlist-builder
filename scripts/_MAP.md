# Scripts

## build_playlist.py
Self-contained Spotify playlist builder. No external dependencies.

### Usage
```bash
python3 build_playlist.py --name "Name" --description "..." --input tracks.json
```

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

### API Endpoints Used
- `POST /api/token` -- refresh token exchange
- `GET /search` -- track and album search (limit 10)
- `GET /albums/{id}/tracks` -- album track listing
- `POST /me/playlists` -- create playlist
- `POST /playlists/{id}/items` -- add tracks to playlist

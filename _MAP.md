# Playlist Builder Skill

## Structure
- `SKILL.md` -- Main skill document with workflow, API reference, and troubleshooting
- `scripts/build_playlist.py` -- Self-contained Python script (stdlib only) that searches Spotify, creates a playlist, and adds tracks
- `scripts/_MAP.md` -- Script directory map

## Key Details
- Uses Feb 2026 Spotify API endpoints (`/me/playlists`, `/playlists/{id}/items`)
- Credentials read from `~/Music/.env`
- No pip dependencies -- uses only Python stdlib (`urllib`, `json`, `base64`)
- Search limit capped at 10 results (Spotify dev mode restriction)
- Retries transient errors (429, 500, 502, 503) with exponential backoff (2s/4s/6s)
- 0.5s delay between requests to avoid 502 cascades (0.1s is too aggressive)
- `--playlist-id` flag for adding to existing playlists (useful for 502 recovery)
- Input: JSON array of `{"artist", "album", "track"}` objects
- Output: JSON with playlist URL, track listing, and not-found entries
- Taste profile files live in `archive-lists/` (not `@archive-lists/`)

## Critical API Gotchas (Feb 2026)
- Response fields renamed: `playlist.tracks` → `playlist.items`, `item.track` → `item.item`
- `DELETE /playlists/{id}/items` is broken (returns 400). Use `PUT .../items` with full URI list instead
- `PUT /playlists/{id}/tracks` returns 403. Use `PUT /playlists/{id}/items` for reordering

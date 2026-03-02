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
- Input: JSON array of `{"artist", "album", "track"}` objects
- Output: JSON with playlist URL, track listing, and not-found entries

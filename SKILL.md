---
name: playlist-builder
description: Build personalized Spotify playlists around any topic, mood, or genre
domains:
  - music
  - spotify
  - playlists
---

# Playlist Builder

Build a Spotify playlist around any topic, mood, genre, or theme -- personalized to the user's listening history.

## When to Use

Activate this skill when the user asks to:
- Build, create, or make a playlist around a topic/mood/genre/theme
- Generate music recommendations and add them to Spotify
- Create a curated playlist based on their taste
- "Make me a playlist about..."
- "Build a playlist for..."

## Prerequisites

- Spotify credentials in `~/Music/.env` with:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
  - `SPOTIFY_REFRESH_TOKEN`
- Python 3 (stdlib only, no pip dependencies)
- The Spotify app must be in Development Mode with the user added as a test user
- User must have Spotify Premium (required for dev mode apps since Feb 2026)

## Workflow

### Step 1: Load Taste Profile

Look for listening history in the working directory at `@archive-lists/` (or `incoming/` as a fallback). Key files:

- **`mp3 Archive.txt`** -- One album per line, format: `Artist - Album`
  ```
  A Tribe Called Quest - The Low End Theory
  Air - Moon Safari
  Mulatu Astatke - Ethiopiques Vol. 4
  ```

- **`Spotify Liked Songs*.txt`** -- One track per line, format: `Track Name\tArtist` (tab-separated, multiple artists joined by `;`)
  ```
  Kingdom of D'mt	Karl Hector & The Malcouns
  God Of The Sun	Skinshape;The Horus All Stars
  Low Sun	Hermanos Gutiérrez
  ```

If no taste files are found, ask the user if they have listening history to share. If none, proceed without personalization.

Read a representative sample (first ~200 lines) from each file to understand the user's taste -- genres, artists, eras, and patterns.

### Step 2: Generate Recommendations

Using your music knowledge combined with the user's taste profile, generate **30-50 album/track recommendations** that fit the requested topic/theme. For each recommendation, provide:

```json
[
  {"artist": "Mulatu Astatke", "album": "Ethiopiques Vol. 4", "track": "Yegelle Tezeta"},
  {"artist": "Khruangbin", "album": "Con Todo El Mundo", "track": "Maria También"}
]
```

Guidelines:
- Mix well-known and deep cuts
- Include tracks the user likely knows AND discoveries they'll enjoy
- The `track` field is optional -- if omitted, the script will pick the most popular track from the album
- Aim for variety within the theme

### Step 3: Write Input File

Write the recommendations as JSON to a temporary file (e.g., `/tmp/playlist_tracks.json`).

### Step 4: Run the Build Script

```bash
python3 ~/.claude/skills/playlist-builder/scripts/build_playlist.py \
  --name "Playlist Name" \
  --description "A short description of the playlist" \
  --input /tmp/playlist_tracks.json
```

### Step 5: Present Results

Read the script's JSON output and present:
- The playlist URL (clickable link)
- How many tracks were found vs. attempted
- The full track listing with artists
- Any tracks that couldn't be found on Spotify

## February 2026 Spotify API Changes

Spotify made major Development Mode API changes effective **February 11, 2026**. These are critical to know:

### Renamed Endpoints (old ones return 403)
| Operation | Old Endpoint (403) | New Endpoint (works) |
|---|---|---|
| Create playlist | `POST /users/{id}/playlists` | `POST /me/playlists` |
| Add tracks | `POST /playlists/{id}/tracks` | `POST /playlists/{id}/items` |
| Remove tracks | `DELETE /playlists/{id}/tracks` | `DELETE /playlists/{id}/items` |
| Save to library | `PUT /me/tracks` | `PUT /me/library` |

### Dev Mode Restrictions
- **Search limit capped at 10** -- using `limit=50` returns `400 Invalid limit`
- **No batch endpoints** -- `GET /tracks`, `GET /albums`, `GET /artists` (plural) eliminated
- **Artist top tracks removed** -- `GET /artists/{id}/top-tracks` returns 403
- **5 test users max** -- apps limited to 5 authorized users
- **Premium required** -- all test users must have Spotify Premium
- **No browse endpoints** -- new releases, categories removed

### Still Available
- `GET /search` (limit max 10)
- `GET /me` and `GET /me/playlists`
- `GET /albums/{id}/tracks` (individual album tracks)
- `GET /tracks/{id}`, `GET /albums/{id}`, `GET /artists/{id}` (individual lookups)
- Player/playback endpoints

## Troubleshooting

### 403 Forbidden on playlist operations
You are using an old endpoint. Check the table above -- use `/me/playlists` for creation and `/playlists/{id}/items` for adding/removing tracks.

### 400 Invalid limit
Search is capped at 10 results in dev mode. Use `limit=5` or `limit=10`.

### 403 on artist top tracks
`GET /artists/{id}/top-tracks` was removed in Feb 2026. Instead, search for tracks by artist name or fetch album tracks via `GET /albums/{id}/tracks`.

### Token issues
If you get 401 errors, the access token may be expired. The script handles refresh automatically via the refresh token in `.env`.

### MCP server conflicts
The Spotify MCP server may cache stale tokens. If using the MCP server alongside this script, be aware they maintain separate token states. The Python script manages its own token refresh independently.

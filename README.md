# Playlist Builder

A [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code/skills) that builds personalized Spotify playlists from natural language. Ask Claude to make you a playlist around any topic, mood, genre, or theme and it will generate recommendations informed by your listening history, search Spotify for each track, and create a playlist in your account.

## How It Works

1. You say something like _"make me a playlist of Ethiopian jazz fusion"_
2. Claude reads your listening history (if available) to understand your taste
3. Claude generates 30-50 track recommendations that fit the theme
4. The Python script searches Spotify, creates a playlist, and adds the tracks
5. You get a link to your new playlist

## Installation

### 1. Clone the skill

```bash
git clone https://github.com/fredbenenson/playlist-builder.git \
  ~/.claude/skills/playlist-builder
```

Or, if you already have it somewhere, symlink it:

```bash
ln -s /path/to/playlist-builder ~/.claude/skills/playlist-builder
```

### 2. Create a Spotify app

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Set the redirect URI to `http://localhost:8888/callback`
4. Note your **Client ID** and **Client Secret**
5. Under **Settings > User Management**, add your Spotify account as a test user (max 5)

> Your Spotify account must have **Premium** -- required for dev mode apps since Feb 2026.

### 3. Get a refresh token

You need a one-time OAuth flow to obtain a refresh token with the right scopes. The simplest way:

```bash
# 1. Open this URL in your browser (replace CLIENT_ID):
#    https://accounts.spotify.com/authorize?client_id=CLIENT_ID&response_type=code&redirect_uri=http://localhost:8888/callback&scope=playlist-modify-private%20playlist-modify-public

# 2. After authorizing, you'll be redirected to localhost with a ?code= parameter.
#    Copy that code and exchange it:

curl -X POST https://accounts.spotify.com/api/token \
  -d grant_type=authorization_code \
  -d code=YOUR_CODE_HERE \
  -d redirect_uri=http://localhost:8888/callback \
  -H "Authorization: Basic $(echo -n 'CLIENT_ID:CLIENT_SECRET' | base64)"

# 3. The response JSON contains your refresh_token.
```

### 4. Create your credentials file

```bash
cat > ~/Music/.env << 'EOF'
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REFRESH_TOKEN=your_refresh_token
EOF
```

### 5. (Optional) Add your listening history

For personalized recommendations, place listening history files in an `@archive-lists/` directory in your working directory:

- **`mp3 Archive.txt`** -- one album per line: `Artist - Album`
- **`Spotify Liked Songs*.txt`** -- tab-separated: `Track Name\tArtist`

Without these, Claude will still build playlists -- just without personalization.

## Usage

Once installed, ask Claude naturally:

```
> make me a playlist of 90s trip-hop deep cuts
> build a chill instrumental playlist for coding
> create a playlist of west african funk from the 70s
```

You can also invoke the skill directly:

```
> /playlist-builder dark ambient for late nights
```

## Requirements

- **Python 3** (stdlib only -- no pip install needed)
- **Spotify Premium** account
- **Claude Code** with skills support

## Troubleshooting

| Problem | Fix |
|---|---|
| `~/Music/.env not found` | Create the credentials file (step 4 above) |
| 401 Unauthorized | Refresh token expired or invalid -- repeat step 3 |
| 403 on playlist creation | Make sure you're on the Feb 2026 endpoints (`/me/playlists`, not `/users/{id}/playlists`) |
| 400 Invalid limit | Dev mode caps search at 10 results -- the script already handles this |
| Tracks not found | Some tracks aren't on Spotify; Claude will report what couldn't be matched |

## Project Structure

```
playlist-builder/
  SKILL.md              # Skill definition and workflow (read by Claude)
  scripts/
    build_playlist.py   # Self-contained Spotify API script (stdlib only)
  README.md             # This file
```

#!/usr/bin/env python3
"""
Spotify Playlist Builder - Self-contained script (stdlib only).

Searches Spotify for tracks, creates a playlist, and adds found tracks.
Uses the Feb 2026 API endpoints (POST /me/playlists, POST /playlists/{id}/items).

Usage:
    python3 build_playlist.py --name "My Playlist" --description "..." --input tracks.json

Input JSON format:
    [
        {"artist": "Artist Name", "album": "Album Name", "track": "Track Name"},
        {"artist": "Artist Name", "album": "Album Name"}
    ]

If "track" is omitted, searches for the most popular track matching the artist + album.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SPOTIFY_API = "https://api.spotify.com/v1"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
ENV_PATH = os.path.expanduser("~/Music/.env")
RATE_LIMIT_DELAY = 0.5  # seconds between API requests (0.1 causes 502 cascades)
MAX_RETRIES = 3  # retries on transient errors (429, 500, 502, 503)


def load_credentials():
    """Load Spotify credentials from .env file."""
    creds = {}
    try:
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip()
    except FileNotFoundError:
        print(f"Error: {ENV_PATH} not found", file=sys.stderr)
        sys.exit(1)

    required = ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN"]
    missing = [k for k in required if k not in creds]
    if missing:
        print(f"Error: Missing keys in .env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return creds


def get_access_token(creds):
    """Exchange refresh token for access token."""
    auth = base64.b64encode(
        f"{creds['SPOTIFY_CLIENT_ID']}:{creds['SPOTIFY_CLIENT_SECRET']}".encode()
    ).decode()
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": creds["SPOTIFY_REFRESH_TOKEN"],
    }).encode()
    req = urllib.request.Request(
        SPOTIFY_TOKEN_URL,
        data=data,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        resp = json.loads(urllib.request.urlopen(req).read())
        return resp["access_token"]
    except (urllib.error.HTTPError, KeyError) as e:
        print(f"Error getting access token: {e}", file=sys.stderr)
        sys.exit(1)


RETRYABLE_STATUS_CODES = {429, 500, 502, 503}


def api_get(url, token):
    """Make authenticated GET request to Spotify API with retry on transient errors."""
    for attempt in range(MAX_RETRIES + 1):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            return json.loads(urllib.request.urlopen(req).read())
        except urllib.error.HTTPError as e:
            if e.code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                wait = (attempt + 1) * 2
                print(f"    Retry {attempt+1}/{MAX_RETRIES} after {e.code}, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            body = e.read().decode()[:200]
            print(f"  GET {e.code}: {url} -- {body}", file=sys.stderr)
            return None
    return None


def api_post(url, payload, token):
    """Make authenticated POST request to Spotify API with retry on transient errors."""
    for attempt in range(MAX_RETRIES + 1):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            return json.loads(urllib.request.urlopen(req).read())
        except urllib.error.HTTPError as e:
            if e.code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                wait = (attempt + 1) * 2
                print(f"    Retry {attempt+1}/{MAX_RETRIES} after {e.code}, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            body = e.read().decode()[:200]
            print(f"  POST {e.code}: {url} -- {body}", file=sys.stderr)
            return None
    return None


def search_track(artist, album, track_name, token):
    """Search for a specific track on Spotify.

    Strategy:
    1. If track_name provided: search for "artist track_name" as track type
    2. If only album: search for "artist album" as album type, then get tracks
    3. Fallback: search for "artist album" as track type, pick most popular
    """
    time.sleep(RATE_LIMIT_DELAY)

    # Strategy 1: Direct track search if track name given
    if track_name:
        q = urllib.parse.quote(f"{artist} {track_name}")
        data = api_get(f"{SPOTIFY_API}/search?q={q}&type=track&limit=10", token)
        if data and data.get("tracks", {}).get("items"):
            tracks = data["tracks"]["items"]
            # Prefer exact-ish artist match
            for t in tracks:
                t_artists = " ".join(a["name"].lower() for a in t["artists"])
                if any(word.lower() in t_artists for word in artist.split()[:2]):
                    return t
            return tracks[0]

    # Strategy 2: Album search -> get album tracks
    if album:
        q = urllib.parse.quote(f"{artist} {album}")
        data = api_get(f"{SPOTIFY_API}/search?q={q}&type=album&limit=5", token)
        if data and data.get("albums", {}).get("items"):
            # Find best matching album
            best_album = None
            for item in data["albums"]["items"]:
                item_artists = " ".join(a["name"].lower() for a in item["artists"])
                if any(word.lower() in item_artists for word in artist.split()[:2]):
                    best_album = item
                    break
            if not best_album:
                best_album = data["albums"]["items"][0]

            time.sleep(RATE_LIMIT_DELAY)
            album_tracks = api_get(
                f"{SPOTIFY_API}/albums/{best_album['id']}/tracks?limit=10", token
            )
            if album_tracks and album_tracks.get("items"):
                # Return the first track (usually a good representative)
                first_track = album_tracks["items"][0]
                return {
                    "uri": first_track["uri"],
                    "name": first_track["name"],
                    "artists": first_track["artists"],
                    "album": {"name": best_album["name"]},
                }

    # Strategy 3: Fallback track search with artist + album
    q = urllib.parse.quote(f"{artist} {album or ''}")
    data = api_get(f"{SPOTIFY_API}/search?q={q}&type=track&limit=10", token)
    if data and data.get("tracks", {}).get("items"):
        tracks = data["tracks"]["items"]
        tracks.sort(key=lambda t: t.get("popularity", 0), reverse=True)
        for t in tracks:
            t_artists = " ".join(a["name"].lower() for a in t["artists"])
            if any(word.lower() in t_artists for word in artist.split()[:2]):
                return t
        return tracks[0]

    return None


def create_playlist(name, description, token):
    """Create a new private playlist via POST /me/playlists."""
    result = api_post(
        f"{SPOTIFY_API}/me/playlists",
        {"name": name, "description": description, "public": False},
        token,
    )
    if not result or "id" not in result:
        print("Error: Failed to create playlist", file=sys.stderr)
        sys.exit(1)
    return result


def add_tracks_to_playlist(playlist_id, track_uris, token):
    """Add tracks to playlist via POST /playlists/{id}/items (Feb 2026 endpoint)."""
    # Spotify accepts max 100 URIs per request
    added = 0
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i : i + 100]
        time.sleep(RATE_LIMIT_DELAY)
        result = api_post(
            f"{SPOTIFY_API}/playlists/{playlist_id}/items",
            {"uris": batch},
            token,
        )
        if result:
            added += len(batch)
        else:
            print(f"  Warning: Failed to add batch starting at index {i}", file=sys.stderr)
    return added


def main():
    parser = argparse.ArgumentParser(description="Build a Spotify playlist")
    parser.add_argument("--name", required=True, help="Playlist name")
    parser.add_argument("--description", default="", help="Playlist description")
    parser.add_argument("--input", required=True, help="Path to JSON input file")
    parser.add_argument("--playlist-id", default=None,
                        help="Add tracks to an existing playlist instead of creating a new one. "
                             "Useful for retrying after 502 failures.")
    args = parser.parse_args()

    # Load input tracks
    try:
        with open(args.input) as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(entries)} entries from {args.input}", file=sys.stderr)

    # Authenticate
    creds = load_credentials()
    token = get_access_token(creds)
    print("Authenticated with Spotify", file=sys.stderr)

    # Search for each track
    found_tracks = []
    not_found = []
    for i, entry in enumerate(entries):
        artist = entry.get("artist", "")
        album = entry.get("album", "")
        track_name = entry.get("track", "")
        label = f"{artist} - {track_name or album}"
        print(f"  [{i+1}/{len(entries)}] Searching: {label}", file=sys.stderr)

        result = search_track(artist, album, track_name, token)
        if result:
            track_artists = ", ".join(a["name"] for a in result.get("artists", []))
            album_name = result.get("album", {}).get("name", "")
            print(f"    Found: {result['name']} by {track_artists}", file=sys.stderr)
            found_tracks.append({
                "uri": result["uri"],
                "name": result["name"],
                "artists": track_artists,
                "album": album_name,
            })
        else:
            print(f"    NOT FOUND", file=sys.stderr)
            not_found.append(label)

    print(f"\nFound {len(found_tracks)}/{len(entries)} tracks", file=sys.stderr)

    if not found_tracks:
        print("No tracks found, aborting", file=sys.stderr)
        sys.exit(1)

    # Create or reuse playlist
    if args.playlist_id:
        playlist_id = args.playlist_id
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        print(f"Adding to existing playlist: {playlist_url}", file=sys.stderr)
    else:
        playlist = create_playlist(args.name, args.description, token)
        playlist_id = playlist["id"]
        playlist_url = playlist.get("external_urls", {}).get("spotify", "")
        print(f"Created playlist: {args.name}", file=sys.stderr)
        print(f"URL: {playlist_url}", file=sys.stderr)

    # Add tracks
    uris = [t["uri"] for t in found_tracks]
    added = add_tracks_to_playlist(playlist_id, uris, token)
    print(f"Added {added} tracks to playlist", file=sys.stderr)

    # Output JSON result to stdout
    output = {
        "playlist_id": playlist_id,
        "playlist_url": playlist_url,
        "playlist_name": args.name,
        "tracks_searched": len(entries),
        "tracks_found": len(found_tracks),
        "tracks_added": added,
        "tracks": found_tracks,
        "not_found": not_found,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

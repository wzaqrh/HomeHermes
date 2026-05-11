---
name: yewtube
category: media
description: >
  Terminal-based YouTube player and downloader with search, playlist management,
  subscription management, and download support. No YouTube API key required.
  Forked from mps-youtube. Replaces the need for browser-based YouTube access
  when searching, playing, or downloading YouTube content from the CLI.
---

# yewtube — Terminal YouTube Client

## Description

yewtube is a terminal-based YouTube player and downloader. No YouTube API key required. It supports searching, playing audio/video, managing playlists, downloading content, and viewing comments — all from the CLI.

## Installation

```bash
# 1. Install player dependency
sudo apt-get install -y mpv

# 2. Install yewtube (pipx recommended)
pipx install yewtube

# For latest development version:
# pipx install git+https://github.com/mps-youtube/yewtube.git
```

Run with the `yt` command.

## Core Usage

### Interactive Mode
```bash
yt
```

Once inside the interactive TUI, key commands:

| Command | Action |
|---------|--------|
| `/ search query` | Search YouTube videos |
| `// playlist name` | Search playlists |
| `1` | Play video #1 from results |
| `1-` | Play all results (from #1 onward) |
| `1[3]` | Loop video #1 three times |
| `4-6[2]` | Loop videos 4-6 twice each |
| `d` | Download current video |
| `set player mpv` | Set mpv as player |
| `h` | Full help |
| `q` | Quit |

### Non-Interactive / Direct Mode
```bash
# Play a specific video URL directly
yt https://www.youtube.com/watch?v=VIDEO_ID

# Search and play first result
yt --search "search keywords"
```

### Upgrading
```bash
pipx upgrade yewtube
```

## Features

- Search and play audio/video from YouTube (no API key)
- Search and import YouTube playlists
- Create and save local playlists
- Download audio/video in various formats/resolutions
- Convert to mp3 and other formats (requires ffmpeg)
- View video comments
- Works with mplayer, mpv, or VLC
- Cross-platform (Linux, macOS, Windows)

## Configuration

Inside `yt` interactive mode, use `set` commands:

```bash
set order views              # Sort results by view count
set columns user:14 date comments rating likes dislikes category:9 views  # Custom columns
set player mpv               # Set mpv as the player
set mpris true               # Enable MPRIS (media player remote control)
```

Configuration is stored at `~/.config/mps-youtube/`.

## Troubleshooting

- **No sound / video not playing**: Ensure mpv is installed: `which mpv`
- **"No player found"**: Run `set player mpv` inside yt, or set the PLAYER env var
- **Search returns no results**: YouTube may be blocking the scrape; retry later or use a VPN
- **Download fails**: Make sure yt-dlp is up to date: `pipx upgrade yt-dlp`
- **yewtube update**: `pipx upgrade yewtube`

## Related Skills

- `youtube-content` — For extracting transcripts from specific YouTube video URLs (complementary: yewtube for discovery/search, youtube-content for transcript extraction)

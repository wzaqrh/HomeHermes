# youtubd Command Reference

Quick command templates for YouTube data collection via yt-dlp.

## Search Videos
```
yt-dlp "ytsearch{N}:{query}" --flat-playlist --dump-json
```
- `N` = count (1-50), `query` = search keywords
- Output: one JSON object per line (id, title, channel, channel_id, duration, view_count, upload_date)

## Get Channel ID from Name
```
yt-dlp "ytsearch1:{channel_name}" --flat-playlist --dump-json
```
Extract `channel_id` from the first result.

## List All Channel Videos
```
yt-dlp "https://www.youtube.com/playlist?list=UU{channel_id[2:]}" --flat-playlist --dump-json
```
Rule: Replace `UC` prefix with `UU` in channel_id.

## List Playlist Videos
```
yt-dlp "https://www.youtube.com/playlist?list={PLAYLIST_ID}" --flat-playlist --dump-json
```

## Get Full Video Details (incl. description, tags)
```
yt-dlp --dump-json "https://www.youtube.com/watch?v={VIDEO_ID}"
```

## Get Subtitles
```
yt-dlp --skip-download --write-subs --sub-langs all --convert-subs srt "URL" -o "/tmp/yt_subs"
cat /tmp/yt_subs.*.srt
```

## Python Parsing Template
```python
import json, subprocess

def search_youtube(query: str, count: int = 10):
    """Search YouTube, return list of video dicts."""
    cmd = f'yt-dlp "ytsearch{count}:{query}" --flat-playlist --dump-json'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return [json.loads(line) for line in result.stdout.strip().split('\n') if line]

def channel_videos(channel_id: str, limit: int = 50):
    """List recent videos from a channel."""
    playlist = 'UU' + channel_id[2:]  # UC → UU
    url = f'https://www.youtube.com/playlist?list={playlist}'
    result = subprocess.run(
        ['yt-dlp', '--flat-playlist', '--dump-json', url],
        capture_output=True, text=True, timeout=60
    )
    videos = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
    return videos[:limit]
```

## YouTube Rate Limiting
- If you get HTTP 429 (Too Many Requests), wait 5-10 seconds and retry
- yt-dlp has built-in retry logic
- Searching is lighter-weight than downloading full metadata

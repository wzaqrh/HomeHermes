---
name: youtube-content
description: >
  Fetch YouTube video transcripts and transform them into structured content
  (chapters, summaries, threads, blog posts). Use when the user shares a YouTube
  URL or video link, asks to summarize a video, requests a transcript, or wants
  to extract and reformat content from any YouTube video.
---

# YouTube Content Tool

Extract transcripts from YouTube videos and convert them into useful formats.

## Setup

```bash
pip install youtube-transcript-api
```

## Helper Script

`SKILL_DIR` is the directory containing this SKILL.md file. The script accepts any standard YouTube URL format, short links (youtu.be), shorts, embeds, live links, or a raw 11-character video ID.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

1. **Fetch** the transcript using the helper script with `--text-only --timestamps`.
2. **Validate**: confirm the output is non-empty and in the expected language. If empty, retry without `--language` to get any available transcript. If still empty, tell the user the video likely has transcripts disabled.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
5. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

## Additional Setup

The helper script (`scripts/fetch_transcript.py`) uses `youtube-transcript-api`, but `yt-dlp` is a more robust alternative for subtitle extraction and is always preferred when the API fails.

```bash
# yt-dlp is installed on this system (via apt/yewtube pipx)
# No additional setup needed
```

## Alternative Method: yt-dlp Subtitle Extraction

When `youtube-transcript-api` fails (empty result, transcript disabled, language mismatch), use `yt-dlp` as fallback:

```bash
# Download subtitles as SRT (all available languages)
yt-dlp --skip-download --write-subs --sub-langs all --convert-subs srt "https://www.youtube.com/watch?v=VIDEO_ID" -o "/tmp/transcript"

# Read the resulting SRT file
cat /tmp/transcript.*.srt
```

**How to use the SRT output:**
- Parse with Python: `pysrt` or manual regex for timestamp + text extraction
- Strip timestamps for plain text
- Pass the text into AI summarization as if it came from the transcript API

**Advantages over youtube-transcript-api:**
- Works on more videos (especially age-restricted, region-locked, or with disabled CC)
- Can auto-generate transcripts (YouTube's auto-captions) when manual subs don't exist
- Supports more subtitle formats (SRT, VTT, TTML, LRC)
- No Python library dependency — uses the already-installed `yt-dlp` binary

## Error Handling

- **Transcript disabled**: first retry with `yt-dlp --skip-download --write-subs` which often works when the API fails. If yt-dlp also can't get subs, tell the user the video has no subtitles and **skip it** — do not fall back to the description text.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user. Also retry with yt-dlp which can auto-generate captions.
- **Dependency missing**: run `pip install youtube-transcript-api` or `python3 -m pip install youtube-transcript-api` and retry. If pip is unavailable, use system package manager or alternate Python installation.
- **yt-dlp not found**: the tool is installed system-wide (`/usr/bin/yt-dlp`) via apt. If missing, install with `sudo apt install yt-dlp` or `pipx install yewtube` (bundles dependencies).
- **No subtitles at all**: fail cleanly. Do NOT use video description, tags, or browser-visual extraction. Description contains no verbatim content and does not justify the token cost of AI summarization.

- **Transcript disabled**: first retry with `yt-dlp --skip-download --write-subs` which often works when the API fails. If yt-dlp also can't get subs, tell the user the video likely has subtitles fully disabled.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user. Also retry with yt-dlp which can auto-generate captions.
- **Dependency missing**: run `pip install youtube-transcript-api` or `python3 -m pip install youtube-transcript-api` and retry. If pip is unavailable, use system package manager or alternate Python installation.
- **yt-dlp not found**: the tool is installed system-wide (`/usr/bin/yt-dlp`) via apt. If missing, install with `sudo apt install yt-dlp` or `pipx install yewtube` (bundles dependencies).
- **Browser access issues**: If YouTube blocks automated access, manually navigate to the video page using browser tools, check for captions/CC button, and extract content visually or via page text.

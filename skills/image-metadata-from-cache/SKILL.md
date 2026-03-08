---
name: image-metadata-from-cache
description: Retrieves textual metadata (title, keywords, description) for images embedded in Obsidian notes from the ai-image-analyzer plugin cache. Use when organizing daily notes, summarizing notes, or when the user mentions image context, embedded images, or understanding images in notes. Read-only; does not modify notes or embeds.
allowed-tools: Read, Glob, Bash
---

# Image Metadata from Cache

Retrieves AI-generated title, keywords, and description for images in a note by reading the **ai-image-analyzer** plugin cache. Run the script with vault root and note path; it returns a JSON array of cached image metadata.

## Instructions

1. **Run the script** with vault root and note path (relative or absolute). The script extracts image refs from the note, resolves paths (bare filename → `Assets/<filename>`; path in link → normalized vault-relative), looks up the plugin cache per image, and outputs JSON.
2. **From the vault:** If skills are symlinked under `.cursor/skills/`, invoke the script via its path (e.g. `.cursor/skills/image-metadata-from-cache/scripts/get_image_metadata.py`). No extra dependencies; stdlib only.

## Script usage

```bash
uv run python .cursor/skills/image-metadata-from-cache/scripts/get_image_metadata.py <vault_path> <note_path>
```

**Example (from vault root):**
```bash
uv run python .cursor/skills/image-metadata-from-cache/scripts/get_image_metadata.py . "00-Inbox/2026-03-07.md"
```

**Arguments:** `vault_path` — Obsidian vault root (directory containing `.obsidian/`). `note_path` — Note file path relative to vault or absolute.

**Output:** JSON array to stdout, one object per cached image (deduplicated by path). Empty array if no images or no cache entries.

```json
[
  { "path": "Assets/Pasted image 20260307180120.png", "text": "Title: ...\nKeywords: ...\nDescription: ..." },
  { "path": "Assets/other.png", "text": "..." }
]
```

## Path resolution

- **Bare filename** (e.g. `![[Pasted image 20260307180120.png]]`) → `Assets/<filename>`.
- **Path in link** (e.g. `![[Assets/foo.png]]` or `![](Assets/foo.png)`) → normalized vault-relative (no leading `/`, forward slashes). Markdown paths are URL-decoded.

All image assets live under `Assets/`; filenames are unique.

## Cache

- Dir: `vault/.obsidian/plugins/ai-image-analyzer/cache/`. Key: MD5 of vault-relative path (no leading slash). Each file: JSON with `path`, `text`, `libVersion`; script returns `path` and `text` only.

## Integration

- **organize-daily-notes:** When a note has embedded images, run this script and use the returned JSON as context for fixes. Do not modify the embeds.
- **assimilate-knowledge / summarize-note:** Optionally run this script to include image descriptions in context.

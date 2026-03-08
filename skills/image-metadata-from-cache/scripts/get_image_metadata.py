#!/usr/bin/env python3
"""
Image Metadata from ai-image-analyzer Cache

Reads a note, extracts embedded image references, resolves paths (bare filenames
→ Assets/<filename>), and returns cached title/keywords/description from the
ai-image-analyzer plugin cache (MD5 path lookup). Stdlib only; no extra deps.

Run with uv from the vault (e.g. cohere-vault):

    uv run python .cursor/skills/image-metadata-from-cache/scripts/get_image_metadata.py <vault_path> <note_path>

Or from this script's directory:

    uv run python get_image_metadata.py <vault_path> <note_path>

Output: JSON array of { "path": "...", "text": "..." } to stdout.
"""

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# Wikilink embed: ![[path]] or ![[path|alias]] or ![[path#anchor]]
WIKILINK_EMBED_RE = re.compile(r"!\[\[([^\]|#]+)(?:[\]|#][^\]]*)?\]\]")
# Markdown image: ![alt](url)
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def resolve_path(link_path: str) -> str:
    """
    Resolve an image reference to a vault-relative path.
    Bare filename (no /) -> Assets/<filename>.
    Otherwise normalize: strip leading /, use forward slashes.
    """
    raw = unquote(link_path).strip()
    normalized = raw.lstrip("/").replace("\\", "/")
    if "/" not in normalized:
        return f"Assets/{normalized}"
    return normalized


def cache_key(vault_relative_path: str) -> str:
    """MD5 of vault-relative path (no leading slash), matching plugin."""
    path = vault_relative_path.lstrip("/")
    return hashlib.md5(path.encode("utf-8")).hexdigest()


def extract_image_refs(content: str) -> list[str]:
    """Extract image reference paths from note content (deduplicated, order preserved)."""
    seen: set[str] = set()
    refs: list[str] = []

    for m in WIKILINK_EMBED_RE.finditer(content):
        linkpath = m.group(1).strip()
        if linkpath and linkpath not in seen:
            seen.add(linkpath)
            refs.append(linkpath)

    for m in MARKDOWN_IMAGE_RE.finditer(content):
        url_path = m.group(1).strip()
        if url_path and url_path not in seen:
            seen.add(url_path)
            refs.append(url_path)

    return refs


def get_image_metadata(vault_root: Path, note_path: Path) -> list[dict[str, str]]:
    """
    Read note at note_path (under vault_root), find image refs, look up cache.
    Returns list of { "path": "...", "text": "..." } for each cached image (deduplicated by path).
    """
    cache_dir = vault_root / ".obsidian" / "plugins" / "ai-image-analyzer" / "cache"
    if not cache_dir.is_dir():
        return []

    note_file = vault_root / note_path if not note_path.is_absolute() else note_path
    if not note_file.is_file():
        return []

    try:
        content = note_file.read_text(encoding="utf-8")
    except OSError:
        return []

    refs = extract_image_refs(content)
    result: list[dict[str, str]] = []
    seen_paths: set[str] = set()

    for ref in refs:
        path = resolve_path(ref)
        if path in seen_paths:
            continue
        key = cache_key(path)
        cache_file = cache_dir / f"{key}.json"
        if not cache_file.is_file():
            continue
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        path_stored = data.get("path") or path
        text = data.get("text")
        if text is not None:
            seen_paths.add(path)
            result.append({"path": path_stored, "text": text})

    return result


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: uv run python get_image_metadata.py <vault_path> <note_path>",
            file=sys.stderr,
        )
        sys.exit(1)

    vault_root = Path(sys.argv[1]).resolve()
    note_path = Path(sys.argv[2])

    if not vault_root.is_dir():
        print(f"Vault path is not a directory: {vault_root}", file=sys.stderr)
        sys.exit(1)

    out = get_image_metadata(vault_root, note_path)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

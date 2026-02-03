#!/usr/bin/env python3
"""
Obsidian Alias Links Resolver

Find and replace alias wikilinks with proper formats:
1. Standalone aliases: [[alias]] → [[actual note name|alias]]
2. Redundant aliases: [[Note Name|Note Name]] → [[Note Name]]
3. Intentional readability aliasing: [[Note|AliasOfNote]] is preserved (where AliasOfNote is a valid alias)

Usage:
    uv run --with pyyaml resolve_alias_links.py scan <directory>
    uv run --with pyyaml resolve_alias_links.py fix <directory>
    uv run --with pyyaml resolve_alias_links.py check <file_path>
    uv run --with pyyaml resolve_alias_links.py resolve <file_path>
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


# Directories to skip when scanning (hidden/system directories)
SKIP_DIRS = {".claude", ".obsidian", ".trash", ".git", "node_modules"}


def should_skip_path(file_path: Path) -> bool:
    """Check if a file path should be skipped based on its directory."""
    parts = file_path.parts
    return any(part in SKIP_DIRS for part in parts)


def extract_frontmatter(content: str) -> tuple[dict[str, Any] | None, str, str]:
    """Extract YAML frontmatter, returning (frontmatter_dict, yaml_text, body)."""
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if match:
        yaml_text = match.group(1)
        body = match.group(2)
        try:
            fm = yaml.safe_load(yaml_text) or {}
            return fm, yaml_text, body
        except yaml.YAMLError:
            return None, yaml_text, body
    return None, "", content


def get_aliases(fm: dict[str, Any]) -> list[str]:
    """Get list of aliases from frontmatter."""
    aliases = fm.get("aliases")
    if aliases is None:
        return []
    if isinstance(aliases, str):
        return [aliases]
    if isinstance(aliases, list):
        return [str(a) for a in aliases if a]
    return []


def build_alias_index(directory: Path) -> dict[str, str]:
    """
    Build index mapping aliases to their actual note names.

    Returns dict where key=alias (case-preserved), value=actual note stem name.
    """
    alias_index: dict[str, str] = {}

    for file_path in directory.rglob("*.md"):
        # Skip hidden/system directories
        if should_skip_path(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            fm, _, _ = extract_frontmatter(content)
            if fm is None:
                continue

            note_name = file_path.stem
            aliases = get_aliases(fm)

            for alias in aliases:
                # Store alias with its original case
                if alias and alias != note_name:
                    alias_index[alias] = note_name
        except Exception:
            continue

    return alias_index


def find_wikilinks_in_text(text: str) -> list[tuple[int, int, str, str | None]]:
    """
    Find all wikilinks in text, returning list of (start, end, link_content, alias_text).

    Returns both direct links [[content]] and aliased links [[content|alias]].
    Excludes section links [[content#section]] and [[content#section|alias]].
    """
    results = []
    # Match [[...]] - both with and without pipes
    pattern = r'\[\[([^\]#]+?)(?:\|([^\]]+?))?\]\]'

    for match in re.finditer(pattern, text):
        link_content = match.group(1).strip()
        alias_text = match.group(2).strip() if match.group(2) else None
        results.append((match.start(), match.end(), link_content, alias_text))

    return results


def find_alias_occurrences(
    content: str,
    alias_index: dict[str, str],
    note_index: dict[str, Path],
) -> list[dict[str, Any]]:
    """
    Find all occurrences of alias wikilinks and redundant aliases that need replacement.

    Cases handled:
    1. [[X]] where X is an alias → replace with [[actual note|X]]
    2. [[X|X]] where alias text matches link content exactly → simplify to [[X]]
    Note: [[Note|AliasOfNote]] is preserved as intentional readability aliasing
    """
    occurrences = []

    # Build case-insensitive lookups
    alias_lower_map = {k.lower(): (k, v) for k, v in alias_index.items()}
    note_lower_map = {n.lower(): n for n in note_index.keys()}

    for start, end, link_content, alias_text in find_wikilinks_in_text(content):
        link_lower = link_content.lower()

        # Case 1: Standalone alias [[X]] where X is an alias
        if alias_text is None:
            # Check if this link content matches an alias
            if link_lower in alias_lower_map:
                original_alias, actual_note = alias_lower_map[link_lower]

                # Skip if the link content itself is also a valid note name
                if link_content in note_index:
                    continue

                # Also skip if lowercase version matches a different note name
                if link_lower in note_lower_map and note_lower_map[link_lower] != actual_note:
                    continue

                occurrences.append({
                    "start": start,
                    "end": end,
                    "original": content[start:end],
                    "type": "alias_link",
                    "alias": link_content,
                    "canonical_alias": original_alias,
                    "actual_note": actual_note,
                    "replacement": f"[[{actual_note}|{original_alias}]]",
                })

        # Case 2: Aliased link [[X|Y]] where Y matches X exactly (redundant: [[Note|Note]])
        else:
            # Check if alias text matches the link content (redundant: [[Note|Note]])
            if link_content == alias_text:
                occurrences.append({
                    "start": start,
                    "end": end,
                    "original": content[start:end],
                    "type": "redundant_alias",
                    "note_name": link_content,
                    "replacement": f"[[{link_content}]]",
                })

    return occurrences


def replace_alias_links(content: str, occurrences: list[dict[str, Any]]) -> str:
    """Replace all alias occurrences in content, working from end to start."""
    # Sort by start position descending to avoid offset issues
    sorted_occs = sorted(occurrences, key=lambda x: x["start"], reverse=True)

    result = content
    for occ in sorted_occs:
        result = result[:occ["start"]] + occ["replacement"] + result[occ["end"]:]

    return result


def build_note_index(directory: Path) -> dict[str, Path]:
    """Build index mapping note names to file paths."""
    index = {}
    for file_path in directory.rglob("*.md"):
        # Skip hidden/system directories
        if should_skip_path(file_path):
            continue
        name = file_path.stem
        index[name] = file_path
    return index


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan directory for alias links that need resolution (dry-run)."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    alias_index = build_alias_index(directory)
    note_index = build_note_index(directory)

    all_occurrences = []
    files_with_aliases = []

    for file_path in directory.rglob("*.md"):
        # Skip hidden/system directories
        if should_skip_path(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            occurrences = find_alias_occurrences(content, alias_index, note_index)

            if occurrences:
                files_with_aliases.append({
                    "file": str(file_path),
                    "count": len(occurrences),
                    "occurrences": occurrences,
                })
                all_occurrences.extend(occurrences)
        except Exception:
            continue

    print(json.dumps({
        "total_aliases_indexed": len(alias_index),
        "total_files_scanned": len(note_index),
        "files_with_alias_links": len(files_with_aliases),
        "total_occurrences": len(all_occurrences),
        "files": files_with_aliases,
    }, indent=2))


def cmd_fix(args: argparse.Namespace) -> None:
    """Fix all alias links in directory."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    alias_index = build_alias_index(directory)
    note_index = build_note_index(directory)

    fixed_files = []
    total_replacements = 0

    for file_path in directory.rglob("*.md"):
        # Skip hidden/system directories
        if should_skip_path(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            occurrences = find_alias_occurrences(content, alias_index, note_index)

            if occurrences:
                new_content = replace_alias_links(content, occurrences)
                file_path.write_text(new_content, encoding="utf-8")

                fixed_files.append({
                    "file": str(file_path),
                    "replacements": len(occurrences),
                    "details": [
                        {"from": o["original"], "to": o["replacement"]}
                        for o in occurrences
                    ],
                })
                total_replacements += len(occurrences)
        except Exception:
            continue

    print(json.dumps({
        "total_aliases_indexed": len(alias_index),
        "files_fixed": len(fixed_files),
        "total_replacements": total_replacements,
        "files": fixed_files,
    }, indent=2))


def cmd_check(args: argparse.Namespace) -> None:
    """Check a single file for alias links."""
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    # Find vault root
    vault_dir = file_path.parent
    while vault_dir.parent != vault_dir:
        if (vault_dir / ".obsidian").exists():
            break
        vault_dir = vault_dir.parent
    else:
        vault_dir = file_path.parent

    alias_index = build_alias_index(vault_dir)
    note_index = build_note_index(vault_dir)

    try:
        content = file_path.read_text(encoding="utf-8")
        occurrences = find_alias_occurrences(content, alias_index, note_index)

        print(json.dumps({
            "file": str(file_path),
            "alias_links_found": len(occurrences),
            "occurrences": occurrences,
        }, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


def cmd_resolve(args: argparse.Namespace) -> None:
    """Resolve alias links in a single file."""
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    # Find vault root
    vault_dir = file_path.parent
    while vault_dir.parent != vault_dir:
        if (vault_dir / ".obsidian").exists():
            break
        vault_dir = vault_dir.parent
    else:
        vault_dir = file_path.parent

    alias_index = build_alias_index(vault_dir)
    note_index = build_note_index(vault_dir)

    try:
        content = file_path.read_text(encoding="utf-8")
        occurrences = find_alias_occurrences(content, alias_index, note_index)

        if occurrences:
            new_content = replace_alias_links(content, occurrences)
            file_path.write_text(new_content, encoding="utf-8")

            print(json.dumps({
                "file": str(file_path),
                "replacements": len(occurrences),
                "details": [
                    {"from": o["original"], "to": o["replacement"]}
                    for o in occurrences
                ],
            }, indent=2))
        else:
            print(json.dumps({
                "file": str(file_path),
                "replacements": 0,
                "message": "No alias links found to resolve",
            }, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


def cmd_aliases(args: argparse.Namespace) -> None:
    """List all aliases indexed from the directory."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    alias_index = build_alias_index(directory)

    # Sort by alias name
    sorted_aliases = sorted(alias_index.items(), key=lambda x: x[0].lower())

    print(json.dumps({
        "total_aliases": len(alias_index),
        "aliases": [
            {"alias": alias, "actual_note": note}
            for alias, note in sorted_aliases
        ],
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find and resolve Obsidian alias wikilinks"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan command
    scan_parser = subparsers.add_parser(
        "scan", help="Scan for alias links (dry-run)"
    )
    scan_parser.add_argument("directory", help="Directory to scan")
    scan_parser.set_defaults(func=cmd_scan)

    # fix command
    fix_parser = subparsers.add_parser(
        "fix", help="Fix all alias links in directory"
    )
    fix_parser.add_argument("directory", help="Directory to fix")
    fix_parser.set_defaults(func=cmd_fix)

    # check command
    check_parser = subparsers.add_parser(
        "check", help="Check single file for alias links"
    )
    check_parser.add_argument("file_path", help="File to check")
    check_parser.set_defaults(func=cmd_check)

    # resolve command
    resolve_parser = subparsers.add_parser(
        "resolve", help="Resolve alias links in single file"
    )
    resolve_parser.add_argument("file_path", help="File to resolve")
    resolve_parser.set_defaults(func=cmd_resolve)

    # aliases command
    aliases_parser = subparsers.add_parser(
        "aliases", help="List all aliases indexed from directory"
    )
    aliases_parser.add_argument("directory", help="Directory to index")
    aliases_parser.set_defaults(func=cmd_aliases)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

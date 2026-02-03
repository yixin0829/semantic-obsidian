#!/usr/bin/env python3
"""
Obsidian Dedupe Links

Deduplicate wikilinks in YAML frontmatter properties using case-insensitive comparison.
Keeps the version with the most capital letters.

Usage:
    uv run --with pyyaml dedupe_links.py scan <directory>
    uv run --with pyyaml dedupe_links.py fix <directory>
    uv run --with pyyaml dedupe_links.py check <file_path>
    uv run --with pyyaml dedupe_links.py dedupe <file_path>
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


# Directories to skip
SKIP_DIRS = {".claude", ".obsidian", ".trash", ".git", "node_modules"}


def count_capitals(s: str) -> int:
    """Count the number of uppercase letters in a string."""
    return sum(1 for c in s if c.isupper())


def extract_wikilink_target(link: str) -> str | None:
    """
    Extract the target note name from a wikilink.
    Handles: [[Note]], [[Note|alias]], [[Note#section]], [[Note#section|alias]]
    Returns the note name only (without section or alias).
    """
    match = re.match(r'\[\[([^\]#|]+)', link)
    if match:
        return match.group(1).strip()
    return None


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


def is_wikilink_array(value: Any) -> bool:
    """Check if a value is a list containing wikilinks."""
    if not isinstance(value, list):
        return False
    if not value:
        return False
    # Check if at least one item looks like a wikilink
    for item in value:
        if isinstance(item, str) and re.search(r'\[\[.+\]\]', item):
            return True
    return False


def dedupe_wikilinks(links: list[str]) -> tuple[list[str], list[str]]:
    """
    Deduplicate a list of wikilink strings case-insensitively.
    Keeps the version with the most capital letters.

    Returns (deduped_list, removed_list).
    """
    # Map: lowercase target -> (original link string, target name, capital count)
    seen: dict[str, tuple[str, str, int]] = {}
    result = []
    removed = []

    for link in links:
        target = extract_wikilink_target(link)
        if target is None:
            # Not a valid wikilink, keep as-is
            result.append(link)
            continue

        key = target.lower()
        capitals = count_capitals(target)

        if key not in seen:
            # First occurrence
            seen[key] = (link, target, capitals)
            result.append(link)
        else:
            # Duplicate found - compare capital counts
            existing_link, existing_target, existing_capitals = seen[key]

            if capitals > existing_capitals:
                # New one has more capitals - replace
                # Remove the old one from result
                result = [r for r in result if r != existing_link]
                removed.append(existing_link)
                # Add the new one
                seen[key] = (link, target, capitals)
                result.append(link)
            else:
                # Existing one wins (or tie - keep first)
                removed.append(link)

    return result, removed


def find_wikilink_properties(fm: dict[str, Any]) -> dict[str, list[str]]:
    """Find all properties that contain wikilink arrays."""
    props = {}
    for key, value in fm.items():
        if is_wikilink_array(value):
            # Extract the string representation of each link
            links = []
            for item in value:
                if isinstance(item, str):
                    links.append(item)
            if links:
                props[key] = links
    return props


def process_file(file_path: Path, dry_run: bool = True) -> dict[str, Any] | None:
    """
    Process a single file for duplicate wikilinks.

    Args:
        file_path: Path to the markdown file
        dry_run: If True, don't modify the file

    Returns:
        Dict with changes info, or None if no duplicates found
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    fm, yaml_text, body = extract_frontmatter(content)
    if fm is None:
        return None

    wikilink_props = find_wikilink_properties(fm)
    if not wikilink_props:
        return None

    changes = {}
    any_changes = False

    for prop, links in wikilink_props.items():
        deduped, removed = dedupe_wikilinks(links)
        if removed:
            changes[prop] = {
                "before": links,
                "after": deduped,
                "removed": removed,
            }
            any_changes = True

    if not any_changes:
        return None

    if not dry_run:
        # Rebuild the YAML frontmatter with deduped links
        new_yaml_lines = []
        lines = yaml_text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this line starts a property we modified
            matched_prop = None
            for prop in changes.keys():
                if re.match(rf"^{re.escape(prop)}:\s*", line):
                    matched_prop = prop
                    break

            if matched_prop:
                # Write the property with deduped values
                new_yaml_lines.append(f"{matched_prop}:")
                for link in changes[matched_prop]["after"]:
                    # Ensure proper quoting
                    if not (link.startswith('"') or link.startswith("'")):
                        link = f'"{link}"'
                    new_yaml_lines.append(f"  - {link}")

                # Skip the original array items
                i += 1
                while i < len(lines) and lines[i].startswith("  - "):
                    i += 1
                continue
            else:
                new_yaml_lines.append(line)

            i += 1

        new_yaml = "\n".join(new_yaml_lines)
        new_content = f"---\n{new_yaml}\n---\n{body}"
        file_path.write_text(new_content, encoding="utf-8")

    return {
        "file": str(file_path),
        "properties": changes,
    }


def should_skip_path(path: Path) -> bool:
    """Check if a path should be skipped."""
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    return False


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan directory for duplicate links (dry-run)."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    files_with_duplicates = []
    total_duplicates = 0
    total_files = 0

    for file_path in directory.rglob("*.md"):
        if should_skip_path(file_path):
            continue

        total_files += 1
        result = process_file(file_path, dry_run=True)

        if result:
            files_with_duplicates.append(result)
            for prop_changes in result["properties"].values():
                total_duplicates += len(prop_changes["removed"])

    print(json.dumps({
        "total_files_scanned": total_files,
        "files_with_duplicates": len(files_with_duplicates),
        "total_duplicates_found": total_duplicates,
        "files": files_with_duplicates,
    }, indent=2))


def cmd_fix(args: argparse.Namespace) -> None:
    """Fix all duplicate links in directory."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    files_fixed = []
    total_duplicates_removed = 0
    total_files = 0

    for file_path in directory.rglob("*.md"):
        if should_skip_path(file_path):
            continue

        total_files += 1
        result = process_file(file_path, dry_run=False)

        if result:
            files_fixed.append(result)
            for prop_changes in result["properties"].values():
                total_duplicates_removed += len(prop_changes["removed"])

    print(json.dumps({
        "total_files_scanned": total_files,
        "files_fixed": len(files_fixed),
        "total_duplicates_removed": total_duplicates_removed,
        "files": files_fixed,
    }, indent=2))


def cmd_check(args: argparse.Namespace) -> None:
    """Check single file for duplicate links (dry-run)."""
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    result = process_file(file_path, dry_run=True)

    if result:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({
            "file": str(file_path),
            "duplicates_found": False,
            "message": "No duplicate wikilinks found",
        }, indent=2))


def cmd_dedupe(args: argparse.Namespace) -> None:
    """Deduplicate links in single file."""
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    result = process_file(file_path, dry_run=False)

    if result:
        result["fixed"] = True
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({
            "file": str(file_path),
            "fixed": False,
            "message": "No duplicate wikilinks found",
        }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deduplicate wikilinks in Obsidian YAML frontmatter"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan command
    scan_parser = subparsers.add_parser(
        "scan", help="Scan for duplicate links (dry-run)"
    )
    scan_parser.add_argument("directory", help="Directory to scan")
    scan_parser.set_defaults(func=cmd_scan)

    # fix command
    fix_parser = subparsers.add_parser(
        "fix", help="Fix all duplicate links"
    )
    fix_parser.add_argument("directory", help="Directory to fix")
    fix_parser.set_defaults(func=cmd_fix)

    # check command
    check_parser = subparsers.add_parser(
        "check", help="Check single file (dry-run)"
    )
    check_parser.add_argument("file_path", help="File to check")
    check_parser.set_defaults(func=cmd_check)

    # dedupe command
    dedupe_parser = subparsers.add_parser(
        "dedupe", help="Deduplicate links in single file"
    )
    dedupe_parser.add_argument("file_path", help="File to dedupe")
    dedupe_parser.set_defaults(func=cmd_dedupe)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

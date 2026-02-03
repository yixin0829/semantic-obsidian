#!/usr/bin/env python3
"""
Obsidian Semantic Links Synchronizer

Validate and sync bidirectional/reversed semantic links in Obsidian YAML frontmatter.

Usage:
    uv run --with pyyaml sync_semantic_links.py validate <directory>
    uv run --with pyyaml sync_semantic_links.py sync <directory>
    uv run --with pyyaml sync_semantic_links.py check <file_path>
    uv run --with pyyaml sync_semantic_links.py fix <file_path>
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


# Semantic link configuration
BIDIRECTIONAL_PROPS = ["RELATED_TO"]
REVERSED_PROPS = {"NEXT": "PRIOR", "PRIOR": "NEXT"}
ALL_SEMANTIC_PROPS = BIDIRECTIONAL_PROPS + list(REVERSED_PROPS.keys())


def extract_wikilink_name(link: str) -> str | None:
    """Extract note name from wikilink format like '[[Note Name]]' or '[[Note Name#Section]]'."""
    match = re.match(r'\[\[([^\]#|]+)', link)
    if match:
        return match.group(1).strip()
    return None


def format_wikilink(name: str) -> str:
    """Format a note name as a quoted wikilink."""
    return f"[[{name}]]"


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


def extract_all_wikilinks(text: str) -> list[str]:
    """Extract all note names from a string that may contain multiple wikilinks."""
    # Find all wikilinks in the text (handles comma-separated format like '[[A]], [[B]]')
    matches = re.findall(r'\[\[([^\]#|]+)', text)
    return [m.strip() for m in matches if m.strip()]


def get_property_links(fm: dict[str, Any], prop: str) -> list[str]:
    """Get list of note names from a frontmatter property."""
    value = fm.get(prop)
    if value is None:
        return []
    if isinstance(value, str):
        # Handle both single wikilink and comma-separated format
        return extract_all_wikilinks(value)
    if isinstance(value, list):
        names = []
        for item in value:
            # Each item could contain multiple wikilinks (comma-separated)
            names.extend(extract_all_wikilinks(str(item)))
        return names
    return []


def build_note_index(directory: Path) -> dict[str, Path]:
    """Build index mapping note names to file paths."""
    index = {}
    for file_path in directory.rglob("*.md"):
        name = file_path.stem
        index[name] = file_path
    return index


def has_inline_wikilinks(value: str) -> bool:
    """Check if a string contains inline wikilinks (single or comma-separated)."""
    # Match any wikilink pattern that's not empty/null
    return bool(re.search(r'\[\[[^\]]+\]\]', value))


def is_multiline_continuation(line: str) -> bool:
    """Check if a line is a YAML multi-line continuation (indented, not array item)."""
    return line.startswith("  ") and not line.strip().startswith("-")


def normalize_frontmatter_format(content: str) -> tuple[str, list[str]]:
    """
    Normalize frontmatter format:
    1. Convert inline wikilinks (single or comma-separated) to multi-line array format
    2. Concatenate multi-line string values into single line

    Returns (new_content, list_of_normalized_properties).
    """
    fm, yaml_text, body = extract_frontmatter(content)
    if fm is None:
        return content, []

    normalized_props = []
    lines = yaml_text.split("\n")
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        matched_prop = False

        # Check if this line is a semantic property with inline wikilinks
        for prop in ALL_SEMANTIC_PROPS:
            prop_match = re.match(rf"^{prop}:\s*(.*)", line)
            if prop_match:
                rest = prop_match.group(1).strip()

                # Check if it has inline wikilinks (single or comma-separated)
                if rest and has_inline_wikilinks(rest):
                    # Extract all wikilinks and convert to multi-line format
                    wikilinks = extract_all_wikilinks(rest)
                    new_lines.append(f"{prop}:")
                    for link in wikilinks:
                        new_lines.append(f'  - "[[{link}]]"')
                    normalized_props.append(prop)
                    matched_prop = True
                    break

        if not matched_prop:
            # Check for multi-line string values (like summary)
            # Pattern: property followed by value, then continuation lines
            prop_match = re.match(r"^(\w+):\s*(.+)$", line)
            if prop_match:
                prop_name = prop_match.group(1)
                first_value = prop_match.group(2)

                # Look ahead for continuation lines
                continuation_lines = []
                j = i + 1
                while j < len(lines) and is_multiline_continuation(lines[j]):
                    continuation_lines.append(lines[j].strip())
                    j += 1

                if continuation_lines:
                    # Concatenate multi-line value into single line
                    full_value = first_value + " " + " ".join(continuation_lines)
                    new_lines.append(f"{prop_name}: {full_value}")
                    normalized_props.append(f"{prop_name} (multiline)")
                    i = j - 1  # Skip the continuation lines (will be incremented at end)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        i += 1

    if normalized_props:
        new_yaml = "\n".join(new_lines)
        return f"---\n{new_yaml}\n---\n{body}", normalized_props

    return content, []


def parse_file(file_path: Path) -> tuple[dict[str, Any] | None, str]:
    """Parse frontmatter from a file, return (frontmatter, full_content)."""
    try:
        content = file_path.read_text(encoding="utf-8")
        fm, _, _ = extract_frontmatter(content)
        return fm, content
    except Exception:
        return None, ""


def add_link_to_property(content: str, prop: str, link_name: str) -> str:
    """Add a wikilink to a frontmatter property using multi-line array format."""
    fm, yaml_text, body = extract_frontmatter(content)
    if fm is None:
        return content

    # Check if link already exists
    existing = get_property_links(fm, prop)
    if link_name in existing:
        return content

    # Build the new link entry
    new_link = f'  - "{format_wikilink(link_name)}"'

    # Find the property in yaml_text and update it
    lines = yaml_text.split("\n")
    new_lines = []
    i = 0
    found = False

    while i < len(lines):
        line = lines[i]

        # Check if this is the target property
        prop_match = re.match(rf"^{prop}:\s*(.*)", line)
        if prop_match:
            found = True
            rest = prop_match.group(1).strip()

            if not rest or rest == "[]" or rest == "null":
                # Empty property, empty array, or null - convert to multi-line
                new_lines.append(f"{prop}:")
                new_lines.append(new_link)
            elif rest.startswith("["):
                # Inline array format - convert to multi-line
                new_lines.append(f"{prop}:")
                # Parse existing inline array items
                inline_items = re.findall(r'"?\[\[([^\]]+)\]\]"?', rest)
                for item in inline_items:
                    new_lines.append(f'  - "[[{item}]]"')
                new_lines.append(new_link)
            elif rest.startswith('"[[') or rest.startswith("'[[") or rest.startswith("[["):
                # Single value on same line - convert to multi-line
                new_lines.append(f"{prop}:")
                # Keep existing value
                if rest.startswith('"') or rest.startswith("'"):
                    new_lines.append(f"  - {rest}")
                else:
                    new_lines.append(f'  - "{rest}"')
                new_lines.append(new_link)
            else:
                # Already multi-line format or other format
                new_lines.append(line)
                # Collect existing array items
                i += 1
                while i < len(lines) and lines[i].startswith("  - "):
                    new_lines.append(lines[i])
                    i += 1
                # Add new link
                new_lines.append(new_link)
                continue
        else:
            new_lines.append(line)
        i += 1

    # If property wasn't found, add it before the closing ---
    if not found:
        new_lines.append(f"{prop}:")
        new_lines.append(new_link)

    new_yaml = "\n".join(new_lines)
    return f"---\n{new_yaml}\n---\n{body}"


def find_issues(
    file_path: Path, fm: dict[str, Any], note_index: dict[str, Path]
) -> list[dict[str, Any]]:
    """Find semantic link issues for a single file.

    Note: Placeholder wikilinks (links to notes that don't exist yet) are
    silently skipped - they are not reported as issues.
    """
    issues = []
    source_name = file_path.stem

    # Check bidirectional properties (e.g., RELATED_TO)
    for prop in BIDIRECTIONAL_PROPS:
        linked_names = get_property_links(fm, prop)
        for target_name in linked_names:
            # Skip placeholder links (notes that don't exist yet)
            if target_name not in note_index:
                continue

            target_path = note_index[target_name]
            target_fm, _ = parse_file(target_path)
            if target_fm is None:
                continue

            target_links = get_property_links(target_fm, prop)
            if source_name not in target_links:
                issues.append({
                    "source": file_path.name,
                    "target": target_path.name,
                    "type": "missing_backlink",
                    "property": prop,
                    "action": f"Add [[{source_name}]] to {target_path.name}'s {prop}",
                })

    # Check reversed properties (e.g., NEXT -> PRIOR)
    for source_prop, target_prop in REVERSED_PROPS.items():
        linked_names = get_property_links(fm, source_prop)
        for target_name in linked_names:
            # Skip placeholder links (notes that don't exist yet)
            if target_name not in note_index:
                continue

            target_path = note_index[target_name]
            target_fm, _ = parse_file(target_path)
            if target_fm is None:
                continue

            target_links = get_property_links(target_fm, target_prop)
            if source_name not in target_links:
                issues.append({
                    "source": file_path.name,
                    "target": target_path.name,
                    "type": "missing_reverse_link",
                    "source_property": source_prop,
                    "target_property": target_prop,
                    "action": f"Add [[{source_name}]] to {target_path.name}'s {target_prop}",
                })

    return issues


def fix_issue(issue: dict[str, Any], note_index: dict[str, Path]) -> bool:
    """Fix a single semantic link issue. Returns True if fixed."""
    if issue["type"] == "target_not_found":
        return False

    source_name = Path(issue["source"]).stem
    target_name = Path(issue["target"]).stem

    if target_name not in note_index:
        return False

    target_path = note_index[target_name]

    try:
        content = target_path.read_text(encoding="utf-8")

        if issue["type"] == "missing_backlink":
            prop = issue["property"]
            new_content = add_link_to_property(content, prop, source_name)
        elif issue["type"] == "missing_reverse_link":
            prop = issue["target_property"]
            new_content = add_link_to_property(content, prop, source_name)
        else:
            return False

        if new_content != content:
            target_path.write_text(new_content, encoding="utf-8")
            return True
    except Exception:
        return False

    return False


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate semantic links in a directory (dry-run)."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    note_index = build_note_index(directory)
    all_issues = []
    files_with_issues = set()

    for file_path in directory.rglob("*.md"):
        fm, _ = parse_file(file_path)
        if fm is None:
            continue

        issues = find_issues(file_path, fm, note_index)
        if issues:
            files_with_issues.add(str(file_path))
            all_issues.extend(issues)

    print(json.dumps({
        "total_files": len(note_index),
        "files_with_issues": len(files_with_issues),
        "total_issues": len(all_issues),
        "issues": all_issues,
    }, indent=2))


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync/fix all broken semantic links in a directory."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    note_index = build_note_index(directory)
    all_issues = []
    fixed_count = 0
    normalized_files = []

    # First pass: normalize comma-separated format in all files
    for file_path in directory.rglob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")
            new_content, normalized_props = normalize_frontmatter_format(content)
            if normalized_props:
                file_path.write_text(new_content, encoding="utf-8")
                normalized_files.append({
                    "file": file_path.name,
                    "properties": normalized_props,
                })
        except Exception:
            continue

    # Second pass: find and fix semantic link issues
    for file_path in directory.rglob("*.md"):
        fm, _ = parse_file(file_path)
        if fm is None:
            continue

        issues = find_issues(file_path, fm, note_index)
        for issue in issues:
            all_issues.append(issue)
            if fix_issue(issue, note_index):
                issue["fixed"] = True
                fixed_count += 1
            else:
                issue["fixed"] = False

    print(json.dumps({
        "total_files": len(note_index),
        "normalized_files": normalized_files,
        "total_issues": len(all_issues),
        "fixed": fixed_count,
        "issues": all_issues,
    }, indent=2))


def cmd_check(args: argparse.Namespace) -> None:
    """Check a single file's semantic links."""
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    # Build index from parent directory (vault root approximation)
    vault_dir = file_path.parent
    # Try to find vault root by looking for common vault indicators
    while vault_dir.parent != vault_dir:
        if (vault_dir / ".obsidian").exists():
            break
        vault_dir = vault_dir.parent
    else:
        vault_dir = file_path.parent

    note_index = build_note_index(vault_dir)
    fm, _ = parse_file(file_path)

    if fm is None:
        print(json.dumps({"error": "Could not parse frontmatter"}))
        sys.exit(1)

    issues = find_issues(file_path, fm, note_index)

    print(json.dumps({
        "file": str(file_path),
        "issues_count": len(issues),
        "issues": issues,
    }, indent=2))


def cmd_fix(args: argparse.Namespace) -> None:
    """Fix a single file's semantic links."""
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    # Build index from vault root
    vault_dir = file_path.parent
    while vault_dir.parent != vault_dir:
        if (vault_dir / ".obsidian").exists():
            break
        vault_dir = vault_dir.parent
    else:
        vault_dir = file_path.parent

    note_index = build_note_index(vault_dir)

    # First: normalize comma-separated format in the source file
    normalized_props = []
    try:
        content = file_path.read_text(encoding="utf-8")
        new_content, normalized_props = normalize_frontmatter_format(content)
        if normalized_props:
            file_path.write_text(new_content, encoding="utf-8")
    except Exception:
        pass

    # Re-parse after normalization
    fm, _ = parse_file(file_path)

    if fm is None:
        print(json.dumps({"error": "Could not parse frontmatter"}))
        sys.exit(1)

    issues = find_issues(file_path, fm, note_index)
    fixed_count = 0

    for issue in issues:
        if fix_issue(issue, note_index):
            issue["fixed"] = True
            fixed_count += 1
        else:
            issue["fixed"] = False

    result = {
        "file": str(file_path),
        "issues_count": len(issues),
        "fixed": fixed_count,
        "issues": issues,
    }

    if normalized_props:
        result["normalized_properties"] = normalized_props

    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and sync Obsidian semantic links"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate semantic links (dry-run)"
    )
    validate_parser.add_argument("directory", help="Directory to validate")
    validate_parser.set_defaults(func=cmd_validate)

    # sync command
    sync_parser = subparsers.add_parser(
        "sync", help="Sync/fix broken semantic links"
    )
    sync_parser.add_argument("directory", help="Directory to sync")
    sync_parser.set_defaults(func=cmd_sync)

    # check command
    check_parser = subparsers.add_parser(
        "check", help="Check single file's semantic links"
    )
    check_parser.add_argument("file_path", help="File to check")
    check_parser.set_defaults(func=cmd_check)

    # fix command
    fix_parser = subparsers.add_parser(
        "fix", help="Fix single file's semantic links"
    )
    fix_parser.add_argument("file_path", help="File to fix")
    fix_parser.set_defaults(func=cmd_fix)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

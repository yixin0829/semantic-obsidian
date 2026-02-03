#!/usr/bin/env python3
"""
Obsidian Frontmatter Parser

Parse and search YAML frontmatter from Obsidian vault markdown files.

Usage:
    uv run --with pyyaml parse_frontmatter.py parse <file_path>
    uv run --with pyyaml parse_frontmatter.py search <directory> <property> <value> [--operator eq|contains|gte|lte]
    uv run --with pyyaml parse_frontmatter.py values <directory> <property>
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


def extract_frontmatter(content: str) -> dict[str, Any] | None:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as e:
            return {"_error": str(e)}
    return None


def parse_file(file_path: Path) -> dict[str, Any] | None:
    """Parse frontmatter from a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        fm = extract_frontmatter(content)
        if fm is not None:
            fm["_file"] = str(file_path)
        return fm
    except Exception as e:
        return {"_file": str(file_path), "_error": str(e)}


def find_markdown_files(directory: Path) -> list[Path]:
    """Find all markdown files in directory recursively."""
    return list(directory.rglob("*.md"))


def normalize_value(value: Any) -> list[str]:
    """Normalize a value to a list of strings for comparison."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def compare_values(
    fm_value: Any, search_value: str, operator: str = "eq"
) -> bool:
    """Compare frontmatter value against search value."""
    fm_values = normalize_value(fm_value)

    if operator == "contains":
        return any(search_value.lower() in v.lower() for v in fm_values)
    elif operator == "eq":
        return any(search_value.lower() == v.lower() for v in fm_values)
    elif operator == "gte":
        return any(v >= search_value for v in fm_values)
    elif operator == "lte":
        return any(v <= search_value for v in fm_values)
    return False


def cmd_parse(args: argparse.Namespace) -> None:
    """Parse and display frontmatter from a single file."""
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    result = parse_file(file_path)
    print(json.dumps(result, indent=2, default=str))


def cmd_search(args: argparse.Namespace) -> None:
    """Search for notes with specific property value."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    files = find_markdown_files(directory)
    matches = []

    for file_path in files:
        fm = parse_file(file_path)
        if fm and "_error" not in fm:
            prop_value = fm.get(args.property)
            if prop_value is not None and compare_values(
                prop_value, args.value, args.operator
            ):
                matches.append(
                    {
                        "file": str(file_path),
                        args.property: prop_value,
                        "summary": fm.get("summary", ""),
                    }
                )

    print(json.dumps({"count": len(matches), "results": matches}, indent=2, default=str))


def cmd_values(args: argparse.Namespace) -> None:
    """List all unique values for a property across directory."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)

    files = find_markdown_files(directory)
    values: dict[str, int] = {}

    for file_path in files:
        fm = parse_file(file_path)
        if fm and "_error" not in fm:
            prop_value = fm.get(args.property)
            if prop_value is not None:
                for v in normalize_value(prop_value):
                    values[v] = values.get(v, 0) + 1

    sorted_values = sorted(values.items(), key=lambda x: (-x[1], x[0]))
    print(
        json.dumps(
            {"property": args.property, "unique_count": len(values), "values": sorted_values},
            indent=2,
            default=str,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse and search Obsidian vault frontmatter"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # parse command
    parse_parser = subparsers.add_parser("parse", help="Parse frontmatter from a file")
    parse_parser.add_argument("file_path", help="Path to markdown file")
    parse_parser.set_defaults(func=cmd_parse)

    # search command
    search_parser = subparsers.add_parser(
        "search", help="Search notes by property value"
    )
    search_parser.add_argument("directory", help="Directory to search")
    search_parser.add_argument("property", help="Property name to search")
    search_parser.add_argument("value", help="Value to match")
    search_parser.add_argument(
        "--operator",
        choices=["eq", "contains", "gte", "lte"],
        default="contains",
        help="Comparison operator (default: contains)",
    )
    search_parser.set_defaults(func=cmd_search)

    # values command
    values_parser = subparsers.add_parser(
        "values", help="List unique values for a property"
    )
    values_parser.add_argument("directory", help="Directory to scan")
    values_parser.add_argument("property", help="Property name")
    values_parser.set_defaults(func=cmd_values)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

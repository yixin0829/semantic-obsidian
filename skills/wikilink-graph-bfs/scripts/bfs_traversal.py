#!/usr/bin/env python3
"""
Obsidian BFS Graph Traversal

Perform breadth-first search traversal on Obsidian notes connected via wikilinks.
Starting from a given note, discover all connected notes up to N hops away.

Usage:
    uv run python bfs_traversal.py traverse <start_note> <n_hops> [directory]
    uv run python bfs_traversal.py graph [directory]
    uv run python bfs_traversal.py neighbors <note> [directory]
"""

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path


# Directories to skip when scanning (only checked relative to scan root)
SKIP_DIRS = {".obsidian", ".trash", ".git", "node_modules"}


def should_skip_path(file_path: Path, root: Path) -> bool:
    """Check if a file path should be skipped based on directories relative to root."""
    try:
        relative = file_path.relative_to(root)
        return any(part in SKIP_DIRS for part in relative.parts)
    except ValueError:
        return False


def extract_wikilinks(content: str) -> list[str]:
    """
    Extract all wikilinks from markdown content.
    
    Returns list of note names (without section anchors or aliases).
    Handles:
    - [[Note Name]]
    - [[Note Name|Display Text]]
    - [[Note Name#Section]]
    - [[Note Name#Section|Display Text]]
    """
    # Match wikilinks, capturing the note name (before # or |)
    pattern = r'\[\[([^\]#|]+)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]'
    matches = re.findall(pattern, content)
    # Strip whitespace and return unique links
    return list(set(link.strip() for link in matches if link.strip()))


def build_note_index(directory: Path) -> dict[str, Path]:
    """Build index mapping note names (stems) to file paths."""
    index = {}
    root = directory.resolve()
    for file_path in directory.rglob("*.md"):
        if should_skip_path(file_path, root):
            continue
        name = file_path.stem
        index[name] = file_path
    return index


def build_graph(directory: Path) -> tuple[dict[str, list[str]], dict[str, Path]]:
    """
    Build adjacency list graph from Obsidian notes.
    
    Returns:
        - adjacency: dict mapping note name to list of linked note names
        - note_index: dict mapping note name to file path
    """
    note_index = build_note_index(directory)
    adjacency: dict[str, list[str]] = {name: [] for name in note_index}
    
    for note_name, file_path in note_index.items():
        try:
            content = file_path.read_text(encoding="utf-8")
            links = extract_wikilinks(content)
            
            # Only include links that point to existing notes
            valid_links = [link for link in links if link in note_index]
            adjacency[note_name] = valid_links
        except Exception:
            continue
    
    return adjacency, note_index


def bfs_traversal(
    start_note: str,
    n_hops: int,
    adjacency: dict[str, list[str]],
    note_index: dict[str, Path],
) -> dict:
    """
    Perform BFS traversal from start_note up to n_hops.
    
    Returns structured result with notes discovered at each level.
    """
    if start_note not in adjacency:
        # Try case-insensitive match
        lower_map = {k.lower(): k for k in adjacency.keys()}
        if start_note.lower() in lower_map:
            start_note = lower_map[start_note.lower()]
        else:
            return {
                "error": f"Note '{start_note}' not found in vault",
                "available_notes": sorted(adjacency.keys())[:20],
            }
    
    visited = {start_note}
    levels: list[dict] = []
    current_level = [start_note]
    
    for hop in range(n_hops + 1):
        level_info = {
            "hop": hop,
            "notes": [],
        }
        
        next_level = []
        for note in current_level:
            note_data = {
                "name": note,
                "path": str(note_index.get(note, "")),
                "outgoing_links": adjacency.get(note, []),
            }
            level_info["notes"].append(note_data)
            
            # Collect neighbors for next level
            if hop < n_hops:
                for neighbor in adjacency.get(note, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.append(neighbor)
        
        levels.append(level_info)
        current_level = next_level
        
        if not current_level:
            break
    
    return {
        "start_note": start_note,
        "max_hops": n_hops,
        "total_notes_discovered": len(visited),
        "levels": levels,
        "all_discovered_notes": sorted(visited),
    }


def cmd_traverse(args: argparse.Namespace) -> None:
    """Perform BFS traversal from a starting note."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)
    
    adjacency, note_index = build_graph(directory)
    result = bfs_traversal(args.start_note, args.n_hops, adjacency, note_index)
    
    print(json.dumps(result, indent=2))


def cmd_graph(args: argparse.Namespace) -> None:
    """Display the full graph structure."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)
    
    adjacency, note_index = build_graph(directory)
    
    # Calculate statistics
    total_edges = sum(len(links) for links in adjacency.values())
    orphan_notes = [name for name, links in adjacency.items() if not links]
    
    # Find incoming links for each note
    incoming: dict[str, list[str]] = {name: [] for name in adjacency}
    for note, links in adjacency.items():
        for link in links:
            incoming[link].append(note)
    
    isolated_notes = [
        name for name in adjacency
        if not adjacency[name] and not incoming[name]
    ]
    
    print(json.dumps({
        "total_notes": len(adjacency),
        "total_edges": total_edges,
        "orphan_notes_count": len(orphan_notes),
        "isolated_notes_count": len(isolated_notes),
        "graph": {
            name: {
                "path": str(note_index[name]),
                "outgoing": links,
                "incoming": incoming[name],
            }
            for name, links in adjacency.items()
        },
    }, indent=2))


def cmd_neighbors(args: argparse.Namespace) -> None:
    """Show direct neighbors (1-hop) of a note."""
    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(1)
    
    adjacency, note_index = build_graph(directory)
    note = args.note
    
    # Case-insensitive lookup
    if note not in adjacency:
        lower_map = {k.lower(): k for k in adjacency.keys()}
        if note.lower() in lower_map:
            note = lower_map[note.lower()]
        else:
            print(json.dumps({
                "error": f"Note '{note}' not found",
                "available_notes": sorted(adjacency.keys())[:20],
            }))
            sys.exit(1)
    
    # Find incoming links
    incoming = [n for n, links in adjacency.items() if note in links]
    
    print(json.dumps({
        "note": note,
        "path": str(note_index[note]),
        "outgoing_links": adjacency[note],
        "incoming_links": incoming,
        "total_connections": len(adjacency[note]) + len(incoming),
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BFS graph traversal on Obsidian notes via wikilinks"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # traverse command
    traverse_parser = subparsers.add_parser(
        "traverse", help="BFS traversal from a starting note"
    )
    traverse_parser.add_argument("start_note", help="Starting note name (without .md)")
    traverse_parser.add_argument("n_hops", type=int, help="Number of hops to traverse")
    traverse_parser.add_argument(
        "directory", nargs="?", default=".",
        help="Vault directory (default: current directory)"
    )
    traverse_parser.set_defaults(func=cmd_traverse)
    
    # graph command
    graph_parser = subparsers.add_parser(
        "graph", help="Display full graph structure"
    )
    graph_parser.add_argument(
        "directory", nargs="?", default=".",
        help="Vault directory (default: current directory)"
    )
    graph_parser.set_defaults(func=cmd_graph)
    
    # neighbors command
    neighbors_parser = subparsers.add_parser(
        "neighbors", help="Show direct neighbors of a note"
    )
    neighbors_parser.add_argument("note", help="Note name to find neighbors for")
    neighbors_parser.add_argument(
        "directory", nargs="?", default=".",
        help="Vault directory (default: current directory)"
    )
    neighbors_parser.set_defaults(func=cmd_neighbors)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

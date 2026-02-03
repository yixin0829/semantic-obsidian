---
name: wikilink-graph-bfs
description: Perform BFS (breadth-first search) graph traversal on notes connected via wikilinks. Use when exploring note relationships, discovering connected knowledge within N hops, mapping knowledge graphs, finding related notes from a starting point, or understanding the link structure around a concept.
---

# Wikilink Graph BFS Traversal

Traverse Obsidian notes as a graph using breadth-first search, starting from any note and discovering connected notes within N hops via wikilinks.

## Quick Start

```bash
# BFS traversal from a note for N hops
uv run python .claude/skills/wikilink-graph-bfs/scripts/bfs_traversal.py traverse "Note Name" 2

# With specific directory
uv run python .claude/skills/wikilink-graph-bfs/scripts/bfs_traversal.py traverse "Note Name" 2 "02-SlipBox"
```

## Choosing N Hops

| N | Use Case |
|---|----------|
| 1 | Direct relationships only |
| 2 | Secondary connections (recommended default) |
| 3 | Broader context |
| 4+ | Comprehensive exploration |

## Commands

| Command | Purpose |
|---------|---------|
| `traverse <note> <n> [dir]` | BFS from note for n hops |
| `graph [dir]` | Full graph structure |
| `neighbors <note> [dir]` | Direct connections of a note |

## Examples

```bash
# Explore 2 hops from Machine Learning
uv run python .claude/skills/wikilink-graph-bfs/scripts/bfs_traversal.py traverse "Machine Learning" 2

# View vault graph structure
uv run python .claude/skills/wikilink-graph-bfs/scripts/bfs_traversal.py graph "."

# Find all neighbors of a note
uv run python .claude/skills/wikilink-graph-bfs/scripts/bfs_traversal.py neighbors "Python"
```

## Reference

For output formats, wikilink parsing details, and behavior notes, see [REFERENCE.md](references/REFERENCE.md).

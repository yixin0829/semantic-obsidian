# BFS Traversal Reference

Technical details for the BFS graph traversal script.

## Output Formats

### Traverse Output

```json
{
  "start_note": "Machine Learning",
  "max_hops": 2,
  "total_notes_discovered": 15,
  "levels": [
    {
      "hop": 0,
      "notes": [
        {
          "name": "Machine Learning",
          "path": "02-SlipBox/Machine Learning.md",
          "outgoing_links": ["Neural Network", "Python", "Statistics"]
        }
      ]
    },
    {
      "hop": 1,
      "notes": [
        {
          "name": "Neural Network",
          "path": "02-SlipBox/Neural Network.md",
          "outgoing_links": ["Deep Learning", "Backpropagation"]
        }
      ]
    }
  ],
  "all_discovered_notes": ["Backpropagation", "Deep Learning", "Machine Learning", "Neural Network", "Python", "Statistics"]
}
```

**Fields:**
- `start_note`: The starting note for traversal
- `max_hops`: Maximum depth requested
- `total_notes_discovered`: Count of all unique notes found
- `levels`: Array of objects, one per hop level (0 = start note)
- `levels[].notes`: Notes discovered at that hop level
- `levels[].notes[].outgoing_links`: All wikilinks from that note (for context)
- `all_discovered_notes`: Sorted list of all discovered note names

### Graph Output

```json
{
  "total_notes": 50,
  "total_edges": 120,
  "orphan_notes_count": 5,
  "isolated_notes_count": 2,
  "graph": {
    "Note Name": {
      "path": "02-SlipBox/Note Name.md",
      "outgoing": ["Linked Note 1", "Linked Note 2"],
      "incoming": ["Note That Links Here"]
    }
  }
}
```

**Fields:**
- `total_notes`: Number of markdown files found
- `total_edges`: Total number of wikilinks (directed edges)
- `orphan_notes_count`: Notes with no outgoing links
- `isolated_notes_count`: Notes with no incoming or outgoing links
- `graph`: Full adjacency list with both directions

### Neighbors Output

```json
{
  "note": "Neural Network",
  "path": "02-SlipBox/Neural Network.md",
  "outgoing_links": ["Deep Learning", "Python"],
  "incoming_links": ["Machine Learning", "CNN"],
  "total_connections": 4
}
```

## Wikilink Parsing

The script extracts note names from all wikilink formats:

| Format | Extracted | Notes |
|--------|-----------|-------|
| `[[Note]]` | Note | Direct link |
| `[[Note\|Alias]]` | Note | Display alias ignored |
| `[[Note#Section]]` | Note | Section anchor stripped |
| `[[Note#Section\|Alias]]` | Note | Both stripped |

**Regex pattern used:**
```python
r'\[\[([^\]#|]+)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]'
```

## Behavior Notes

- **Case-insensitive lookup**: Note names are matched case-insensitively
- **Existing notes only**: Links to non-existent notes are excluded from the graph
- **Skipped directories**: `.obsidian`, `.trash`, `.git`, `node_modules` are ignored
- **Orphan vs Isolated**:
  - Orphan: No outgoing links (may have incoming)
  - Isolated: No links in either direction

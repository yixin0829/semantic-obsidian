---
name: knowledge-review
description: Review and strengthen SlipBox knowledge through random exploration. Randomly selects a note from 02-SlipBox/, traverses wikilinks (1-3 hops), and identifies outdated info, contradictions, missing connections, and schema gaps. Trigger: "accommodate", "review my knowledge", "random walk", "explore connections", or "audit my notes".
---

# Knowledge Review

## Workflow

### 1. Select Random Starting Note

```bash
find 02-SlipBox -name "*.md" -type f | shuf -n 1
```

Read the selected note. Note its core concept, existing wikilinks (TOPIC, RELATED_TO, inline), and tag type.

### 2. Explore Connections (1-3 Hops)

Use the `wikilink-graph-bfs` skill for structured exploration.

Track exploration path: `[[Start]] → [[Hop1]] → [[Hop2]]`

### 3. Review for Issues

At each note, check for:

- **Outdated:** Facts that may have changed, stale references, dead wikilinks
- **Contradictions:** Conflicting claims or inconsistent definitions across notes
- **Missing connections:** Notes that should link but don't, concepts without wikilinks, empty RELATED_TO
- **Schema gaps:** Sparse Overview sections, missing examples, incomplete TOPIC hierarchy

### 4. Search for Hidden Connections

Search SlipBox for notes sharing key concepts from the walk that aren't already linked.

### 5. Output Report

Format as:
- **Walk path:** `[[A]] → [[B]] → [[C]]`
- **Issues found:** Group by type (Outdated, Contradictions, Missing connections, Schema gaps)
- **Recommended actions:** Numbered list with specific edits

### 6. Apply Fixes

For each action, confirm with user before editing. Show the specific change and rationale.

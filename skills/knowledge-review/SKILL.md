---
name: knowledge-review
description: Review and strengthen SlipBox knowledge through random exploration. Randomly selects a note from 02-SlipBox/, traverses wikilinks (1-3 hops), and identifies outdated info, contradictions, missing connections, and schema gaps. Trigger: "accommodate", "review my knowledge", "random walk", "explore connections", or "audit my notes".
allowed-tools: Bash, Read, Edit
---

# Knowledge Review

## Workflow

### 1. Select Random Starting Note

```bash
obsidian random:read folder="02-SlipBox"
```

This selects AND reads a random note in one command. Note its core concept, existing wikilinks (TOPIC, RELATED_TO, inline), and tag type.

### 2. Explore Connections (1-3 Hops)

Use the `wikilink-graph-bfs` skill for structured multi-hop BFS exploration.

At each hop, enrich the analysis with direct link queries:
```bash
obsidian backlinks file="<Note Name>"   # what links here?
obsidian links file="<Note Name>"       # what does it link to?
```

Track exploration path: `[[Start]] → [[Hop1]] → [[Hop2]]`

### 3. Review for Issues

At each note, check for:

- **Outdated:** Facts that may have changed, stale references
- **Dead wikilinks:** Check for broken links:
  ```bash
  obsidian links file="<Note Name>"    # list outgoing links
  obsidian unresolved                  # vault-wide broken link detection
  ```
- **Contradictions:** Conflicting claims or inconsistent definitions across notes
- **Missing connections:** Notes that should link but don't, concepts without wikilinks, empty RELATED_TO
- **Schema gaps:** Sparse Overview sections, missing examples, incomplete TOPIC hierarchy

### 4. Search for Hidden Connections

Use the obsidian CLI to find notes sharing key concepts from the walk that aren't already linked:

```bash
obsidian search query="<key concept>" path="02-SlipBox" format=json
```

### 5. Output Report

Format as:
- **Walk path:** `[[A]] → [[B]] → [[C]]`
- **Issues found:** Group by type (Outdated, Dead wikilinks, Contradictions, Missing connections, Schema gaps)
- **Recommended actions:** Numbered list with specific edits

### 6. Apply Fixes

For each action, confirm with user before editing.

- **Metadata fixes** (scalar properties like dates):
  ```bash
  obsidian property:set name=last_updated value=<YYYY-MM-DD> type=date file="<Note Name>"
  ```
- **Content additions/corrections** and **list-type property edits** (tags, TOPIC, RELATED_TO): Use the Edit tool for targeted insertions and replacements.

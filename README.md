# Semantic Obsidian

Agent skills for making your Obsidian vault semantic. This Claude Code plugin provides tools for managing wikilinks, frontmatter metadata, and semantic relationships in your notes.

## Installation

### Via Marketplace

```shell
/plugin marketplace add yixin0829/semantic-obsidian
/plugin install semantic-skills@semantic-obsidian
```

### Manually
Copy the `skills/` directory into your relevant AI IDE folder, e.g. `.claude/skills/` for Claude Code. Refer to [Claude Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) and [Agent Skills](https://agentskills.io/home) for more information.

## Skills

This plugin includes 10 skills for managing your Obsidian vault:

| Skill | Description |
|-------|-------------|
| `resolve-alias-links` | Convert alias wikilinks `[[alias]]` to explicit format `[[note\|alias]]` |
| `assimilate-knowledge` | Integrate new knowledge into SlipBox notes |
| `wikilink-graph-bfs` | BFS traversal on wikilink graph to explore note relationships |
| `dedupe-frontmatter-links` | Remove duplicate wikilinks in YAML frontmatter properties |
| `frontmatter-parser` | Parse and query YAML frontmatter metadata |
| `knowledge-review` | Random walk through notes to review and strengthen knowledge |
| `summarize-note` | Generate AI summaries for markdown notes using Ollama and populate frontmatter `summary` property |
| `sync-semantic-links` | Validate and sync bidirectional semantic links (RELATED_TO, PRIOR/NEXT) |
| `organize-daily-notes` | Clean up and organize daily notes — fix spelling, grammar, capitalization, and markdown structure |

## Usage Examples

### Resolve alias links
```
Scan my vault for alias links and convert them to explicit format
```

### Explore note connections
```
Do a BFS traversal starting from "Machine Learning" for 2 hops
```

### Review knowledge
```
Review my knowledge - pick a random note and audit its connections
```

### Sync semantic links
```
Validate all RELATED_TO links are bidirectional in my SlipBox
```

### Assimilate knowledge
```
Assimilate this new concept into my SlipBox notes
```

### Dedupe frontmatter links
```
Remove duplicate wikilinks from frontmatter properties in my vault
```

### Summarize notes
```
Summarize all my SlipBox notes using qwen3:8b.
```

### Parse frontmatter
```
Find all notes with tag "slip-box/concept"
```

### Organize daily notes
```
Clean up my daily notes from the past week
```

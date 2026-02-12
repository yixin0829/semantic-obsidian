---
name: obsidian-cli
description: >
  Interact with Obsidian vaults via the `obsidian` CLI. Use when asked to: read or
  write daily notes, search vault content, analyze note connections (backlinks,
  outgoing links, orphans, dead-ends), manage frontmatter properties and tags,
  create notes from templates, list or inspect files, open workspaces, track tasks,
  manage bookmarks, view note outlines, or navigate multi-vault setups. Trigger on
  any request involving Obsidian vault interaction, note management, or knowledge
  base operations.
allowed-tools: Bash
---

# Obsidian CLI

All commands: `obsidian <command> [options]`

## Core Patterns

**Vault targeting** (multi-vault):
```bash
obsidian vault=MyVault <command>
```

**File targeting** (two methods):
```bash
obsidian read file="Note Name"      # by filename (without extension)
obsidian read path="folder/note.md" # by relative path from vault root
```

## Workflow Decision Tree

**Modifying a note?**
- Add content at top → `prepend` / `daily:prepend`
- Add content at bottom → `append` / `daily:append`
- Change metadata → `property:set` / `property:remove`
- Rename or relocate → `move`

**Creating a note?**
- Template exists for this type → `create name=<n> template=<t>`
- Custom content → `create name=<n> content=<text>`
- Will populate later → `create name=<n>`

**Investigating a note's connections?**
- What links here? → `backlinks`
- What does it link to? → `links`
- What's its structure? → `outline`

**Auditing vault health?**
- Notes nobody links to → `orphans`
- Notes that link to nothing → `deadends`
- Broken links → `unresolved`

**Finding information?**
- Full-text search → `search query=<text>`
- Browse by tag → `tag name=<tag>`
- Serendipity → `random:read`
- Recent context → `recents`

## Workflow Examples

```bash
# Log to daily note
obsidian daily:prepend content="## Meeting Notes\n- Discussed timeline"

# Analyze connections around a note
obsidian backlinks file="Machine Learning"
obsidian links file="Machine Learning"

# Create from template
obsidian templates
obsidian create name="New Concept" template="SlipBox Template"

# Search, read, and inspect structure
obsidian search query="neural networks" format=json limit=10
obsidian read file="Neural Networks"
obsidian outline file="Neural Networks" format=tree
```

## References

Load the relevant reference when you need full command syntax and options:

- **Investigating note relationships** or **auditing vault link health** → [graph-analysis.md](references/graph-analysis.md) — `backlinks`, `links`, `orphans`, `deadends`, `unresolved`
- **Reading, creating, or modifying note content** → [content-ops.md](references/content-ops.md) — `read`, `create`, `append`, `prepend`, `delete`, `move`, `open`, `daily:*`, `templates`, `outline`
- **Working with frontmatter properties, tags, or tasks** → [metadata.md](references/metadata.md) — `properties`, `property:read/set/remove`, `tags`, `aliases`, `tasks`
- **Searching, browsing vault structure, or managing workspace** → [search-and-vault.md](references/search-and-vault.md) — `search`, `vault`, `files`, `folders`, `workspace`, `bookmarks`, `recents`

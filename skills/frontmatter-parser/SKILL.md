---
name: frontmatter-parser
description: Parse YAML frontmatter from markdown notes into structured data. Use when searching, filtering, or querying notes by their metadata properties (created, tags, author, summary, TOPIC, PRIOR, NEXT, RELATED_TO, etc.). Enables quick property-based searches across the vault.
allowed-tools: Read, Grep, Glob, Bash
---

# Frontmatter Parser

Parse and query YAML frontmatter metadata from Obsidian vault markdown files.

## Instructions

1. **Single File Parsing**: Use `Read` tool to view a markdown file, then extract YAML between opening `---` and closing `---` delimiters at the start of the file.

2. **Batch Parsing**: Use the Python helper script at `.claude/skills/frontmatter-parser/scripts/parse_frontmatter.py` for efficient batch operations:
   ```bash
   uv run --with pyyaml .claude/skills/frontmatter-parser/scripts/parse_frontmatter.py <command> [args]
   ```

3. **Property Search**: To find notes with specific property values, use the helper script's search capabilities or combine `Grep` with `Read`.

## Helper Script Commands

```bash
# Parse single file and output JSON
uv run --with pyyaml .claude/skills/frontmatter-parser/scripts/parse_frontmatter.py parse <file_path>

# Search for notes with specific property value
uv run --with pyyaml .claude/skills/frontmatter-parser/scripts/parse_frontmatter.py search <directory> <property> <value>

# List all unique values for a property across directory
uv run --with pyyaml .claude/skills/frontmatter-parser/scripts/parse_frontmatter.py values <directory> <property>
```

## Vault Property Schema

Based on `02-SlipBox/Obsidian Property.md`, these are the standard properties:

### Core Properties (Universal)
| Property | Type | Description |
|----------|------|-------------|
| `created` | Date (YYYY-MM-DD) | Note creation date |
| `last_updated` | Date (YYYY-MM-DD) | Last modification date |
| `author` | Array of strings | Note authors/contributors |
| `tags` | Array of strings | Hierarchical structural tags |
| `aliases` | Array of strings | Alternative names for linking |
| `summary` | String | Brief description of content |

### Zettelkasten Properties
| Property | Type | Description |
|----------|------|-------------|
| `TOPIC` | Array of wikilinks | Main topic categorization |
| `PRIOR` | Array of wikilinks | Prerequisite/previous notes |
| `NEXT` | Array of wikilinks | Follow-up notes |
| `RELATED_TO` | Array of wikilinks | Cross-references |

### Project-Specific Properties
| Property | Type | Description |
|----------|------|-------------|
| `start_dt` | Date | Project start date |
| `end_dt` | Date or null | Project completion date |
| `cloud_drive` | URL | External storage link |
| `project` | Array of wikilinks | Associated projects |

### Reference-Specific Properties
| Property | Type | Description |
|----------|------|-------------|
| `title` | String | Original title of work |
| `url` | URL | Link to original source |
| `year` | Number | Publication year |
| `zotero_uri` | URI | Zotero item link |
| `published` | Date | Publication date |

## Examples

### Find all notes by a specific author
```bash
uv run --with pyyaml .claude/skills/frontmatter-parser/scripts/parse_frontmatter.py search "02-SlipBox" author "Yixin Tian"
```

### List all unique tags in the vault
```bash
uv run --with pyyaml .claude/skills/frontmatter-parser/scripts/parse_frontmatter.py values "." tags
```

### Find notes created after a specific date
```bash
uv run --with pyyaml .claude/skills/frontmatter-parser/scripts/parse_frontmatter.py search "." created "2025-01-01" --operator gte
```

### Find notes with specific tag
```bash
uv run --with pyyaml .claude/skills/frontmatter-parser/scripts/parse_frontmatter.py search "." tags "slip-box/concept"
```

## YAML Frontmatter Format

```yaml
---
created: 2025-09-27
last_updated: 2025-12-08
author:
  - Yixin Tian
tags:
  - slip-box/concept
aliases:
  - Alternative Name
summary: Brief description of note content
TOPIC:
  - "[[Parent Topic]]"
PRIOR:
  - "[[Prerequisite Note]]"
NEXT:
  - "[[Follow-up Note]]"
RELATED_TO:
  - "[[Related Concept 1]]"
  - "[[Related Concept 2]]"
---
```

## Notes

- Wikilinks in frontmatter use format: `"[[Note Name]]"` (quoted)
- Arrays use multi-line YAML format with `- ` prefix
- Empty arrays use `[]`
- Null/empty values leave the property with no value after colon
- Tags are hierarchical using `/` separator (e.g., `ref/media/books`)

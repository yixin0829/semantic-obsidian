---
name: resolve-alias-links
description: Find and replace standalone alias wikilinks [[alias]] with their full format [[actual note name|alias]]. Use when normalizing wikilink syntax, cleaning up alias references, or ensuring links display with custom text while pointing to the correct note.
allowed-tools: Read, Grep, Glob, Bash
---

# Resolve Alias Links

Find and replace standalone alias wikilinks with their full explicit format.

## Problem

In Obsidian, notes can have aliases defined in YAML frontmatter:

```yaml
aliases:
  - LLM
  - Large Language Models
```

Users often link to notes using these aliases: `[[LLM]]`. While Obsidian resolves these links correctly, they can cause issues:

1. **Ambiguity**: It's unclear whether `[[LLM]]` refers to a note named "LLM" or is an alias
2. **Dataview queries**: Alias links may not be resolved properly in some query contexts
3. **Export/portability**: External tools may not understand alias resolution

## Solution

This skill converts standalone alias wikilinks to explicit format:

- **Before**: `[[LLM]]`
- **After**: `[[Large Language Model|LLM]]`

This makes the link explicit while preserving the display text.

## Instructions

Use the Python helper script at `.claude/skills/resolve-alias-links/scripts/resolve_alias_links.py`:

```bash
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py <command> [args]
```

## Helper Script Commands

```bash
# Scan directory for alias links (dry-run, shows what would be changed)
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py scan <directory>

# Fix all alias links in directory
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py fix <directory>

# Check single file for alias links (dry-run)
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py check <file_path>

# Resolve alias links in single file
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py resolve <file_path>

# List all aliases indexed from directory
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py aliases <directory>
```

## Examples

### Scan SlipBox for alias links
```bash
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py scan "02-SlipBox"
```

### Fix all alias links in the vault
```bash
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py fix "."
```

### Check a single note
```bash
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py check "02-SlipBox/Large Language Model.md"
```

### List all aliases in the vault
```bash
uv run --with pyyaml .claude/skills/resolve-alias-links/scripts/resolve_alias_links.py aliases "."
```

## Detection Rules

A wikilink `[[X]]` is identified as an alias link if:

1. **X matches an alias** defined in some note's frontmatter
2. **X is NOT itself a note name** (to avoid false positives)
3. **X does NOT contain a pipe** (already explicit: `[[Note|X]]`)
4. **X does NOT contain a hash** (section links: `[[Note#Section]]`)

## Output Format

The script outputs JSON with scan/fix results:

```json
{
  "total_aliases_indexed": 216,
  "files_with_alias_links": 5,
  "total_occurrences": 12,
  "files": [
    {
      "file": "02-SlipBox/Large Language Model.md",
      "count": 1,
      "occurrences": [
        {
          "original": "[[LLM]]",
          "alias": "LLM",
          "actual_note": "Large Language Model",
          "replacement": "[[Large Language Model|LLM]]"
        }
      ]
    }
  ]
}
```

## Wikilink Formats

| Format | Description | Handled |
|--------|-------------|---------|
| `[[Note]]` | Direct link | Checked for alias match |
| `[[Note\|Alias]]` | Explicit alias | Skipped (already explicit) |
| `[[Note#Section]]` | Section link | Skipped |
| `[[Note#Section\|Text]]` | Section with alias | Skipped |

## Notes

- The script builds an alias index from all notes in the target directory
- Aliases are matched case-insensitively but preserve original case in replacement
- Links in YAML frontmatter (inside `---` delimiters) are also processed
- Always run `scan` first to preview changes before using `fix`
- Automatically skips hidden/system directories: `.claude`, `.obsidian`, `.trash`, `.git`, `node_modules`

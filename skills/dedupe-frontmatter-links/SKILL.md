---
name: dedupe-frontmatter-links
description: Deduplicate wikilinks in any YAML frontmatter property that contains multi-line wikilink arrays. Removes case-insensitive duplicates like [[ml]] and [[ML]], keeping the version with more capital letters. Use when cleaning up frontmatter, fixing duplicate links, or normalizing link casing.
allowed-tools: Read, Grep, Glob, Bash
---

# Dedupe Frontmatter Links

Deduplicate wikilinks in YAML frontmatter properties using case-insensitive comparison.

## Problem

In Obsidian, users may accidentally add duplicate wikilinks to frontmatter properties that differ only in case:

```yaml
RELATED_TO:
  - "[[ml]]"
  - "[[ML]]"
  - "[[Machine Learning]]"
```

These duplicates clutter the frontmatter and can cause issues with queries and navigation.

## Solution

This skill identifies and removes case-insensitive duplicate wikilinks, keeping the version with the most capital letters (as it's typically the more "canonical" form):

- **Before**: `[[ml]]`, `[[ML]]`, `[[Ml]]`
- **After**: `[[ML]]` (most capitals wins)

## Instructions

Use the Python helper script at `.claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py`:

```bash
uv run --with pyyaml .claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py <command> [args]
```

## Helper Script Commands

```bash
# Scan directory for duplicate links (dry-run, shows what would be changed)
uv run --with pyyaml .claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py scan <directory>

# Fix all duplicate links in directory
uv run --with pyyaml .claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py fix <directory>

# Check single file for duplicate links (dry-run)
uv run --with pyyaml .claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py check <file_path>

# Deduplicate links in single file
uv run --with pyyaml .claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py dedupe <file_path>
```

## Examples

### Scan SlipBox for duplicate links
```bash
uv run --with pyyaml .claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py scan "02-SlipBox"
```

### Fix all duplicates in the vault
```bash
uv run --with pyyaml .claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py fix "."
```

### Check a single note
```bash
uv run --with pyyaml .claude/skills/dedupe-frontmatter-links/scripts/dedupe_links.py check "02-SlipBox/Machine Learning.md"
```

## Deduplication Rules

1. **Case-insensitive matching**: `[[ml]]` and `[[ML]]` are considered duplicates
2. **Prefer more capitals**: When duplicates exist, keep the version with most uppercase letters
3. **Tie-breaker**: If capital count is equal, keep the first occurrence
4. **Any wikilink array property**: Processes any frontmatter property that contains multi-line wikilink arrays
5. **Preserves order**: Non-duplicate links maintain their original order

## Output Format

The script outputs JSON with scan/fix results:

```json
{
  "total_files_scanned": 100,
  "files_with_duplicates": 3,
  "total_duplicates_found": 7,
  "files": [
    {
      "file": "02-SlipBox/Machine Learning.md",
      "properties": {
        "RELATED_TO": {
          "before": ["[[ml]]", "[[ML]]", "[[deep learning]]"],
          "after": ["[[ML]]", "[[deep learning]]"],
          "removed": ["[[ml]]"]
        }
      }
    }
  ]
}
```

## Notes

- The script automatically detects any property with multi-line wikilink array values
- The script skips hidden/system directories: `.claude`, `.obsidian`, `.trash`, `.git`, `node_modules`
- Always run `scan` first to preview changes before using `fix`
- Links with different display text (e.g., `[[ML|machine learning]]`) are compared by their target only
- Section links (e.g., `[[Note#Section]]`) compare only the note name portion

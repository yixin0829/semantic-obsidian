---
name: sync-semantic-links
description: Validate and sync bidirectional semantic links in YAML frontmatter. Ensures RELATED_TO links are mutual between notes, and PRIOR/NEXT links are properly reversed. Use when checking link consistency, fixing broken bidirectional relationships, or maintaining Zettelkasten semantic properties.
allowed-tools: Read, Grep, Glob, Bash
---

# Sync Semantic Links

Validate and synchronize semantic relationship properties (PRIOR, NEXT, RELATED_TO) in Obsidian vault frontmatter.

## Semantic Link Types

### Bidirectional Properties
Properties where both notes should reference each other symmetrically:

| Property | Description |
|----------|-------------|
| `RELATED_TO` | Mutual relationship - if A links to B, B should link to A |

### Reversed Properties
Property pairs where the relationship is directional but reciprocal:

| Source Property | Target Property | Description |
|-----------------|-----------------|-------------|
| `NEXT` | `PRIOR` | If A has B in NEXT, B should have A in PRIOR |
| `PRIOR` | `NEXT` | If A has B in PRIOR, B should have A in NEXT |

## Instructions

Use the Python helper script at `.claude/skills/sync-semantic-links/scripts/sync_semantic_links.py`:

```bash
uv run --with pyyaml .claude/skills/sync-semantic-links/scripts/sync_semantic_links.py <command> [args]
```

## Helper Script Commands

```bash
# Validate all semantic links in a directory (dry-run, no changes)
uv run --with pyyaml .claude/skills/sync-semantic-links/scripts/sync_semantic_links.py validate <directory>

# Sync/fix all broken semantic links in a directory
uv run --with pyyaml .claude/skills/sync-semantic-links/scripts/sync_semantic_links.py sync <directory>

# Check a single file's semantic links
uv run --with pyyaml .claude/skills/sync-semantic-links/scripts/sync_semantic_links.py check <file_path>

# Fix a single file's semantic links (updates linked notes)
uv run --with pyyaml .claude/skills/sync-semantic-links/scripts/sync_semantic_links.py fix <file_path>
```

## Examples

### Validate all SlipBox notes
```bash
uv run --with pyyaml .claude/skills/sync-semantic-links/scripts/sync_semantic_links.py validate "02-SlipBox"
```

### Fix broken links across the vault
```bash
uv run --with pyyaml .claude/skills/sync-semantic-links/scripts/sync_semantic_links.py sync "02-SlipBox"
```

### Check single note relationships
```bash
uv run --with pyyaml .claude/skills/sync-semantic-links/scripts/sync_semantic_links.py check "02-SlipBox/Knowledge Graph.md"
```

## Link Format Convention

Links in frontmatter use multi-line YAML array format with quoted wikilinks:

```yaml
RELATED_TO:
  - "[[Note A]]"
  - "[[Note B]]"
PRIOR:
  - "[[Previous Note]]"
NEXT:
  - "[[Following Note]]"
```

## Validation Rules

1. **Format Normalization**:
   - Comma-separated wikilinks like `'[[A]], [[B]], [[C]]'` are automatically converted to multi-line YAML array format
   - This normalization happens before semantic link validation

2. **RELATED_TO** (bidirectional):
   - If `Note A` has `[[Note B]]` in RELATED_TO
   - Then `Note B` must have `[[Note A]]` in RELATED_TO
   - If missing, add `- "[[Note A]]"` to Note B's RELATED_TO

3. **PRIOR/NEXT** (reversed):
   - If `Note A` has `[[Note B]]` in NEXT
   - Then `Note B` must have `[[Note A]]` in PRIOR
   - If missing, add `- "[[Note A]]"` to Note B's PRIOR

4. **Placeholder Links**:
   - Wikilinks to notes that don't exist yet are silently skipped
   - These are treated as intentional placeholders for future notes

5. **Note Resolution**:
   - Wikilinks are resolved by filename (without path)

## Output Format

The script outputs JSON with validation results:

```json
{
  "total_files": 100,
  "files_with_issues": 5,
  "issues": [
    {
      "source": "Note A.md",
      "target": "Note B.md",
      "type": "missing_backlink",
      "property": "RELATED_TO",
      "action": "add [[Note A]] to Note B's RELATED_TO"
    }
  ],
  "fixed": 5
}
```

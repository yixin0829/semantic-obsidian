# Graph Analysis

## backlinks

```bash
obsidian backlinks file=<name>
obsidian backlinks path=<path>
obsidian backlinks file=<name> counts    # link count per source file
obsidian backlinks file=<name> total     # total count only
```

## links

```bash
obsidian links file=<name>
obsidian links path=<path>
obsidian links file=<name> total
```

## orphans

Files with no incoming links.

```bash
obsidian orphans
obsidian orphans total
obsidian orphans all       # include non-markdown files
```

## deadends

Files with no outgoing links.

```bash
obsidian deadends
obsidian deadends total
obsidian deadends all      # include non-markdown files
```

## unresolved

Links pointing to files that don't exist.

```bash
obsidian unresolved
obsidian unresolved total
obsidian unresolved counts    # count per unresolved target
obsidian unresolved verbose   # show source files for each
```

## Vault Health Audit

```bash
# 1. Find isolated notes
obsidian orphans total
obsidian deadends total

# 2. Find broken links
obsidian unresolved verbose

# 3. Investigate a specific note
obsidian backlinks file="Suspect Note" counts
obsidian links file="Suspect Note"
```

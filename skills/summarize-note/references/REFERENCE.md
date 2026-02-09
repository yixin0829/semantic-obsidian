# Summarize Note Reference

Technical details for the note summarization script.

## Architecture

```
┌─────────────┐
│  .md file    │
└──────┬──────┘
       │ read + parse frontmatter
       ▼
┌─────────────────────┐
│  Skip check         │  summary exists and does NOT start with [AI]?
│  (human summary?)   │  → skip, return immediately
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Markdown header    │  split on #, ##, ### boundaries
│  splitter           │  track header breadcrumb per section
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Section merger     │  merge small adjacent sections up to chunk_size
│  + recursive split  │  further split oversized sections by ¶ / \n / . / space
└──────┬──────────────┘
       │
       ▼
  ┌────┴────┐
  │ 1 chunk │──────────► STUFF_PROMPT → single Ollama call
  └─────────┘
  ┌────┴────┐
  │ N chunks│──────────► MAP_PROMPT × N (concurrent via asyncio.gather)
  └────┬────┘                │
       │              N section summaries
       ▼                     │
  COMBINE_PROMPT ◄───────────┘
       │
       ▼
  Final summary string
       │
       ▼
┌─────────────────────┐
│  Write frontmatter  │  summary: "[AI] ..."
└─────────────────────┘
```

## Splitting pipeline

### Stage 1: Markdown header splitter (`split_by_markdown_headers`)

Splits text on `#`, `##`, `###` heading lines (configurable via `levels`).
Each resulting `Section` carries a breadcrumb dict:

```python
Section(
    content="Body text between headings...",
    headers={"h1": "Python", "h2": "Strings", "h3": "f-String"}
)
```

When a higher-level heading appears, all deeper levels are cleared from the
breadcrumb (e.g. a new `##` clears any `h3`).

The heading line itself is excluded from `content`.

### Stage 2: Section merging (`split_note`)

Adjacent small sections are merged into chunks up to `chunk_size` characters,
joined by `\n\n`. Each section is prefixed with its breadcrumb for LLM context:

```
[Python > Strings > f-String]
A better way to write string after python 3.6...
```

This prevents the pathological case where a note with many short subsections
produces hundreds of tiny chunks (e.g. 107 chunks → 1 after merging at 50K).

### Stage 3: Recursive character splitter (`split_text_recursively`)

Applies only when a single section exceeds `chunk_size`. Tries separators in
priority order:

| Priority | Separator | Splits on |
|----------|-----------|-----------|
| 1        | `\n\n`    | Paragraph breaks |
| 2        | `\n`      | Line breaks |
| 3        | `. `      | Sentence boundaries |
| 4        | ` `       | Word boundaries |

If no separator is found, falls back to a hard character cut.
When a part still exceeds `chunk_size` after splitting, it recurses with the
remaining (lower-priority) separators.

## Summarization strategy

| Chunks | Strategy | Ollama calls |
|--------|----------|--------------|
| 1      | **Stuff** — entire note sent as one prompt | 1 |
| N > 1  | **Map-reduce** — map all chunks concurrently, then reduce | N + 1 |

Map calls use `asyncio.gather` for concurrent execution. Ollama queues
concurrent requests internally, so this is beneficial when the server has
capacity (e.g. multiple GPUs or batched inference).

The reduce step receives section summaries formatted as:

```
Section 1: <summary>

Section 2: <summary>

...
```

## Prompt design

Four prompt components work together:

| Component | Role | Key constraints |
|-----------|------|-----------------|
| `SYSTEM_MSG` | Sets summarizer persona | No fabrication; preserve source terminology; no meta-commentary |
| `MAP_PROMPT` | Summarize one chunk | Acknowledges breadcrumb format; asks for arguments + data points |
| `COMBINE_PROMPT` | Synthesize section summaries | Requires unified narrative (not concatenation); 3-6 sentences |
| `STUFF_PROMPT` | Summarize a short/single-chunk note | Same as combine; adds stub/placeholder detection |

Prompts use `{text}` as the interpolation marker, replaced via `.replace()`
(not `.format()`) to avoid `KeyError` when note content contains curly braces.

## Skip logic

The script checks the existing `summary` frontmatter property before processing:

| Existing summary | Behavior |
|------------------|----------|
| Empty or absent  | Process normally (generate AI summary) |
| Starts with `[AI]` | Process normally (overwrite previous AI summary) |
| Any other value  | **Skip** — treated as human-written |

This ensures human summaries are never overwritten by the script.

## Frontmatter handling

### Reading

Frontmatter is extracted via regex matching `---\n...\n---` at the start of
the file. The raw YAML text is preserved separately from the parsed dict to
enable surgical line-level edits without re-serializing the entire YAML
(which would reorder keys and lose formatting).

### Writing

The `summary` field is updated by line-matching `^summary:\s*` in the raw
YAML text. If no `summary` line exists, one is inserted before the first
Zettelkasten property (`TOPIC`, `PRIOR`, `NEXT`, `RELATED_TO`).

The value is always written as:

```yaml
summary: "[AI] The generated summary text here."
```

Double quotes inside the summary are escaped as `\"`.

## Output formats

### Successful summarization

```json
{
  "file": "path/to/note.md",
  "chunks": 3,
  "old_summary": "[AI] Previous summary...",
  "new_summary": "[AI] New summary...",
  "updated": true
}
```

### Skipped (human summary)

```json
{
  "file": "path/to/note.md",
  "skipped": true,
  "reason": "Human summary exists (does not start with [AI])",
  "summary": "The existing human summary."
}
```

### Error

```json
{
  "file": "path/to/note.md",
  "error": "Description of what went wrong"
}
```

## LLM output cleaning

The `clean_llm_output` function post-processes model responses:

1. Strips `<think>...</think>` blocks (Qwen3 and other thinking models)
2. Removes wrapping single or double quotes
3. Strips leading/trailing whitespace

## Dependencies

Only two runtime dependencies beyond the Python standard library:

| Package | Purpose |
|---------|---------|
| `ollama` | Async client for the Ollama REST API |
| `pyyaml` | YAML frontmatter parsing |

Both are installed ephemerally via `uv run --with ollama,pyyaml`.

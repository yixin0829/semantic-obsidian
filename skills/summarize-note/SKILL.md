---
name: summarize-note
description: >
  Generate AI summaries for markdown notes using Ollama and populate the
  frontmatter `summary` property. Use hierarchical map-reduce for notes
  exceeding model context. Trigger when asked to summarize notes, generate
  note abstracts, add AI summaries to frontmatter, or batch-summarize
  Obsidian vault notes.
allowed-tools: Read, Grep, Glob, Bash
---

## Instructions

1. Ask the user which Ollama model to use (e.g., `qwen3:8b`, `llama3`, `gemma2`). The model must already be pulled in Ollama.

2. Dry-run first to preview summaries without modifying files:
   ```bash
   uv run --with ollama,pyyaml \
       skills/summarize-note/scripts/summarize_note.py <model> --dry-run <file_path> [...]
   ```

3. If summaries look good, run without `--dry-run` to write them:
   ```bash
   uv run --with ollama,pyyaml \
       skills/summarize-note/scripts/summarize_note.py <model> <file_path> [...]
   ```

4. Review the JSON output to confirm summaries were generated and written correctly.

## Key behaviors

- Notes with an existing human summary (no `[AI]` prefix) are skipped automatically.
- Long notes are split by headings and summarized via concurrent map-reduce.
- Thinking model tags (e.g. `<think>`) are stripped automatically.
- Use `--chunk-size` to adjust for models with smaller context windows (default: 50000 chars, ~12K tokens, sized for 32K+ context models).
- Use `--base-url` to point to a remote Ollama instance.

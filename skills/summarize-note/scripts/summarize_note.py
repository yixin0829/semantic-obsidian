#!/usr/bin/env python3
"""
Obsidian Note Summarizer

Generate AI summaries for Obsidian markdown notes using Ollama.
Uses hierarchical summarization (map-reduce with concurrent map calls)
for long notes that exceed model context.

Dependencies: ollama, pyyaml

Usage:
    uv run --with ollama,pyyaml summarize_note.py <model> <file_path> [...]

Examples:
    uv run --with ollama,pyyaml summarize_note.py qwen3:8b "path/to/note.md"
    uv run --with ollama,pyyaml summarize_note.py qwen3:8b --dry-run "note1.md" "note2.md"
"""

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from ollama import AsyncClient


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_MSG = (
    "You are an expert summarizer for a personal knowledge base. "
    "You produce concise, information-dense summaries that capture the "
    "core substance of the source material. "
    "Rules:\n"
    "- Output ONLY the summary text. No headings, labels, bullet points, "
    "or meta-commentary (e.g. do NOT start with \"This section...\", "
    "\"The note discusses...\", or \"Summary:\").\n"
    "- Write in plain, direct prose. Prefer concrete claims over vague "
    "generalizations.\n"
    "- Preserve key terminology, names, and technical concepts from the "
    "source rather than paraphrasing them into generic language.\n"
    "- CRITICAL: You may ONLY use facts explicitly stated in the source. "
    "NEVER fabricate, infer, or generate information beyond what is written. "
)

MAP_PROMPT = (
    "Below is a chunk from a longer markdown note. The chunk may contain "
    "one or more sections; header breadcrumbs in square brackets (e.g. "
    "\"[Topic > Subtopic]\") indicate the section hierarchy.\n\n"
    "Write a concise summary of this chunk. Capture the main arguments, "
    "key concepts, and any concrete examples or data points. Omit "
    "boilerplate, formatting artifacts, and navigational text.\n\n"
    "---\n{text}\n---"
)

COMBINE_PROMPT = (
    "Below are summaries of consecutive chunks from a single markdown note. "
    "Synthesize them into ONE cohesive paragraph that functions as an "
    "abstract of the entire note.\n\n"
    "Requirements:\n"
    "- The paragraph should let a reader understand the note's scope, "
    "core argument or content, and key takeaways without reading the "
    "original.\n"
    "- Synthesize the chunk summaries into a unified narrative; do NOT "
    "simply concatenate or list them.\n"
    "- Keep it concise (3-6 sentences).\n\n"
    "---\n{text}\n---"
)

STUFF_PROMPT = (
    "Below is a short markdown note. Write ONE concise paragraph that "
    "functions as an abstract of the note.\n\n"
    "Requirements:\n"
    "- A reader should understand the note's scope, core argument or "
    "content, and key takeaways from this paragraph alone.\n"
    "- Keep it concise (2-5 sentences). Preserve key terms and names.\n"
    "- CRITICAL: If the note body is a placeholder (e.g. \"{Content}\"), "
    "a stub, or contains very little substantive text, output ONLY a "
    "brief one-sentence description of what the note title refers to using your general knowledge. "
    "Do NOT expand placeholders or invent details that are not present.\n\n"
    "---\n{text}\n---"
)


# ---------------------------------------------------------------------------
# Markdown header splitter
# ---------------------------------------------------------------------------

@dataclass
class Section:
    """A section of markdown text with its header breadcrumb."""
    content: str
    headers: dict[str, str] = field(default_factory=dict)


def split_by_markdown_headers(
    text: str,
    levels: list[int] | None = None,
) -> list[Section]:
    """Split markdown text on heading lines, tracking the header hierarchy.

    Args:
        text: Raw markdown body (no frontmatter).
        levels: Which heading levels to split on (default [1, 2, 3]).

    Returns:
        A list of Sections.  Each Section.content is the text between
        headings (excluding the heading line itself).  Section.headers
        carries the breadcrumb, e.g. {"h1": "Python", "h2": "Strings"}.
    """
    if levels is None:
        levels = [1, 2, 3]

    sections: list[Section] = []
    current_headers: dict[str, str] = {}
    current_lines: list[str] = []

    for line in text.split("\n"):
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            if level in levels:
                # flush accumulated lines
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append(Section(body, dict(current_headers)))
                current_lines = []

                # update breadcrumb: set this level, clear deeper levels
                current_headers[f"h{level}"] = m.group(2).strip()
                for lvl in levels:
                    if lvl > level:
                        current_headers.pop(f"h{lvl}", None)
                continue

        current_lines.append(line)

    # last section
    body = "\n".join(current_lines).strip()
    if body:
        sections.append(Section(body, dict(current_headers)))

    return sections


# ---------------------------------------------------------------------------
# Recursive character splitter
# ---------------------------------------------------------------------------

def split_text_recursively(
    text: str,
    chunk_size: int,
    separators: list[str] | None = None,
) -> list[str]:
    """Split *text* into pieces of at most *chunk_size* characters.

    Tries each separator in order; when a piece is still too large it
    falls back to the next separator.  Final fallback is a hard cut.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " "]

    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # pick the first separator that appears in the text
    sep = None
    for s in separators:
        if s in text:
            sep = s
            break

    if sep is None:
        # hard split
        chunks: list[str] = []
        for i in range(0, len(text), chunk_size):
            piece = text[i : i + chunk_size].strip()
            if piece:
                chunks.append(piece)
        return chunks

    parts = text.split(sep)
    chunks = []
    current: list[str] = []
    current_len = 0

    for part in parts:
        added_len = len(part) + (len(sep) if current else 0)
        if current_len + added_len <= chunk_size:
            current.append(part)
            current_len += added_len
        else:
            if current:
                chunks.append(sep.join(current).strip())
            if len(part) > chunk_size:
                # recurse with remaining separators
                remaining = separators[separators.index(sep) + 1 :]
                chunks.extend(
                    split_text_recursively(part, chunk_size, remaining)
                )
                current = []
                current_len = 0
            else:
                current = [part]
                current_len = len(part)

    if current:
        piece = sep.join(current).strip()
        if piece:
            chunks.append(piece)

    return chunks


# ---------------------------------------------------------------------------
# Combined note splitter
# ---------------------------------------------------------------------------

def _section_text(sec: Section) -> str:
    """Build the text for a section, including its header breadcrumb."""
    prefix = ""
    if sec.headers:
        crumbs = " > ".join(sec.headers.values())
        prefix = f"[{crumbs}]\n"
    return prefix + sec.content


def split_note(body: str, chunk_size: int) -> list[str]:
    """Split a note body into LLM-ready chunks.

    1. Split by markdown headings for structural awareness.
    2. Merge small adjacent sections into chunks up to *chunk_size*.
    3. Further split oversized sections via recursive character splitting.
    """
    sections = split_by_markdown_headers(body)

    if not sections:
        return split_text_recursively(body, chunk_size)

    # Merge small adjacent sections into chunks up to chunk_size
    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for sec in sections:
        text = _section_text(sec)
        if not text.strip():
            continue

        if len(text) > chunk_size:
            # Flush anything accumulated so far
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_len = 0
            # Split the oversized section itself
            chunks.extend(split_text_recursively(text, chunk_size))
        elif current_len + len(text) + 2 > chunk_size:
            # Adding this section would exceed the limit; flush and start new
            if current_parts:
                chunks.append("\n\n".join(current_parts))
            current_parts = [text]
            current_len = len(text)
        else:
            current_parts.append(text)
            current_len += len(text) + 2  # account for "\n\n" joiner

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return [c for c in chunks if c.strip()]


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def extract_frontmatter_and_body(content: str) -> tuple[dict | None, str, str]:
    """Return (parsed_dict, raw_yaml_text, body_after_frontmatter)."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if m:
        yaml_text, body = m.group(1), m.group(2)
        try:
            fm = yaml.safe_load(yaml_text) or {}
            return fm, yaml_text, body
        except yaml.YAMLError:
            return None, yaml_text, body
    return None, "", content


def update_summary_in_yaml(yaml_text: str, new_summary: str) -> str:
    """Replace or insert the ``summary`` field in raw YAML text."""
    escaped = new_summary.replace("\\", "\\\\").replace('"', '\\"')
    summary_line = f'summary: "[AI] {escaped}"'

    lines = yaml_text.split("\n")
    new_lines: list[str] = []
    found = False

    for line in lines:
        if re.match(r"^summary:\s*", line):
            new_lines.append(summary_line)
            found = True
        else:
            new_lines.append(line)

    if not found:
        insert_idx = len(new_lines)
        for i, line in enumerate(new_lines):
            if re.match(r"^(TOPIC|PRIOR|NEXT|RELATED_TO):", line):
                insert_idx = i
                break
        new_lines.insert(insert_idx, summary_line)

    return "\n".join(new_lines)


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def clean_llm_output(text: str) -> str:
    """Strip thinking tags, wrapping quotes, and whitespace."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        text = text[1:-1]
    return text.strip()


async def _call_ollama(
    client: AsyncClient, model: str, prompt: str
) -> str:
    """Send a chat request to Ollama and return the cleaned response."""
    resp = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": prompt},
        ],
    )
    return clean_llm_output(resp.message.content)


async def summarize_chunks(
    client: AsyncClient, model: str, chunks: list[str]
) -> str:
    """Summarize using stuff (1 chunk) or concurrent map-reduce (many)."""
    if len(chunks) == 1:
        return await _call_ollama(
            client, model, STUFF_PROMPT.replace("{text}", chunks[0])
        )

    # --- map step: concurrent calls ---
    tasks = [
        _call_ollama(client, model, MAP_PROMPT.replace("{text}", chunk))
        for chunk in chunks
    ]
    section_summaries: list[str] = await asyncio.gather(*tasks)

    # --- reduce step ---
    combined = "\n\n".join(
        f"Section {i + 1}: {s}" for i, s in enumerate(section_summaries)
    )
    return await _call_ollama(
        client, model, COMBINE_PROMPT.replace("{text}", combined)
    )


# ---------------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------------

async def process_file(
    client: AsyncClient,
    model: str,
    file_path: Path,
    chunk_size: int,
    dry_run: bool = False,
) -> dict:
    """Generate a summary for one markdown file and optionally write it back."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"file": str(file_path), "error": str(e)}

    fm, yaml_text, body = extract_frontmatter_and_body(content)
    if fm is None:
        return {"file": str(file_path), "error": "No valid frontmatter found"}
    if not body.strip():
        return {"file": str(file_path), "error": "No content to summarize"}

    old_summary = fm.get("summary", "")

    # Skip notes that have a human-written summary (not prefixed with [AI])
    if old_summary and not str(old_summary).startswith("[AI]"):
        return {
            "file": str(file_path),
            "skipped": True,
            "reason": "Human summary exists (does not start with [AI])",
            "summary": old_summary,
        }

    print("  Splitting note into chunks...", file=sys.stderr)
    chunks = split_note(body.strip(), chunk_size)
    print(f"  {len(chunks)} chunk(s) to process", file=sys.stderr)

    if not chunks:
        return {"file": str(file_path), "error": "No content after splitting"}

    try:
        print(f"  Generating summary via Ollama ({model})...", file=sys.stderr)
        summary = await summarize_chunks(client, model, chunks)
    except Exception as e:
        return {"file": str(file_path), "error": f"Summarization failed: {e}"}

    result = {
        "file": str(file_path),
        "chunks": len(chunks),
        "old_summary": old_summary,
        "new_summary": f"[AI] {summary}",
        "updated": False,
    }

    if not dry_run:
        new_yaml = update_summary_in_yaml(yaml_text, summary)
        new_content = f"---\n{new_yaml}\n---\n{body}"
        file_path.write_text(new_content, encoding="utf-8")
        result["updated"] = True

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def _run(args: argparse.Namespace) -> None:
    client = AsyncClient(host=args.base_url)

    results: list[dict] = []
    for file_str in args.files:
        fp = Path(file_str)
        if not fp.exists():
            results.append({"file": file_str, "error": "File not found"})
            continue
        if fp.suffix != ".md":
            results.append({"file": file_str, "error": "Not a markdown file"})
            continue

        print(f"Summarizing: {fp.name}", file=sys.stderr)
        result = await process_file(client, args.model, fp, args.chunk_size, args.dry_run)
        results.append(result)

        if result.get("skipped"):
            print(f"  Skipped: {result['reason']}", file=sys.stderr)
        elif "error" not in result:
            print("  Done.", file=sys.stderr)
        else:
            print(f"  Error: {result['error']}", file=sys.stderr)

    print(json.dumps(results, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate AI summaries for Obsidian markdown notes using Ollama"
    )
    parser.add_argument("model", help="Ollama model name (e.g., qwen3:8b)")
    parser.add_argument("files", nargs="+", help="Markdown file path(s)")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50000,
        help="Max chunk size in characters (default: 50000, ~12K tokens)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview summaries without modifying files",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama API base URL (default: http://localhost:11434)",
    )

    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()

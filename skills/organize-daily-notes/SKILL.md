---
name: organize-daily-notes
description: Organize and clean up Obsidian daily notes over a configurable time range (default past 3 days). Fixes spelling, grammar, capitalization, and markdown structure; organizes loose text; resolves implicit mentions of project/slipbox/reference notes to wikilinks. When notes contain embedded images, use the image-metadata-from-cache skill to attach AI-generated image descriptions as context. Use when the user mentions cleaning up daily notes, organizing daily logs, tidying notes, fixing spelling, improving note formatting, entity linking, or making daily notes more readable.
allowed-tools: Read, Edit, Write, Glob, Bash, Agent
---

# Organize Daily Notes

Clean up and organize Obsidian daily notes for improved readability and consistency. This skill fixes spelling, grammar, capitalization, and markdown structure while strictly preserving all content.

## Core Principle

**Never delete information.** The goal is to reorganize and polish, not to curate.

## Canonical Daily Note Structure

Daily notes live in `00-Inbox/YYYY-MM-DD.md`. The expected section order is:

```markdown
# YYYY-MM-DD

## Priority
(Rendered Preview — never modify this)
![[Top 3 Things]]

## Backlog
(task query code blocks — never modify these)

## Daily Log
(main content (Yixin's experience & learning): tasks, events, meetings, learnings, ideas)

### HH:MM Activity Title
(subsection for timed activities with significant content)

## Quick Notes
(optional ad-hoc captures: images, web links, ideas, quick reminders/todos, brainstorm sessions, etc.)
```

## Cleanup Categories

Work through these categories for each note. Not every note will have issues in every category — skip notes that are already clean.

### 1. Spelling and Typos

Fix clear misspellings. Common patterns to watch for:
- Transposed letters: "tempaltes" → "templates", "typologically" → "topologically"
- Missing letters: "serveral" → "several"
- Wrong words: "incoming portfolio" → "income portfolio" (context-dependent)
- Code/tool names: respect official casing (e.g., "Firestore" not "firestore" when referring to the product)

### 2. Proper Noun Capitalization

Capitalize product names, service names, and personal names consistently:
- **Tech products**: LinkedIn, GitHub, Firebase, Firestore, OpenAI, Wealthsimple, Obsidian, Tailscale, OAuth, MagicDNS
- **Personal names**: Always capitalize (e.g., "stacey" → "Stacey")
- **Place names**: "red river" → "Red River"
- When in doubt about whether something is a proper noun, leave it as-is

### 3. Grammar and Sentence Structure

- **Capitalize first word** of standalone bullet points (not sub-items that continue a sentence)
- **Fix verb tense**: "CLI stops works" → "CLI stopped working", "Edith send" → "Edith sent"
- **Fix word choice**: "Here's now you" → "Here's how you", "softwares" → "software"
- **Abbreviations**: "colab" → "collaboration" only if it's clearly a typo (not a reference to Google Colab)
- Keep the user's informal/shorthand voice in quick notes — don't over-formalize

### 4. Time Format Standardization

- Use 24-hour format consistently: "20:30pm" → "20:30" (remove redundant am/pm)
- Remove extra spaces: "10: 30" → "10:30"
- Capitalize activity names after timestamps: "16:09 practiced" → "16:09 Practiced"

### 5. Markdown Structure

This is the most impactful category. Fix these structural issues:

**Section ordering**: If sections are out of order, rearrange them. The correct order is Priority > Backlog > Daily Log > Quick Notes.

**Heading levels**: Ensure proper hierarchy:
- `##` for main sections (Priority, Backlog, Daily Log, Quick Notes)
- `###` for timed activities or major topics within Daily Log
- `####` for sub-topics within activities
- `#####` for further nesting

When restructuring, adjust all child headings to maintain relative depth. If a `##` heading becomes `###`, its `###` children become `####`.

**Loose/floating text**: Text that sits outside any section or bullet structure should be organized:
- If it belongs to a nearby bullet list, indent it as a sub-bullet
- If it's a standalone thought, make it a bullet point
- If it's a continuation of a section, place it under the appropriate heading
- When it's unclear which section it belongs to, prefer the section it's closest to, or ask the user

### 6. Security Flagging

If you notice plaintext secrets, API keys, tokens, or passwords, flag them to the user in your summary. Do not delete them — the user may need them. Just note: "File X contains plaintext API keys/tokens that should be rotated if this vault is shared."

### 7. Entity Linking

Resolve plain-text mentions of existing vault notes to wikilinks. **Only add new links; never remove or change existing wikilinks** (including placeholders to notes that don't exist yet).

**Linkable notes:** Notes in `01-Project/`, `02-Slipbox/`, and `03-Reference/`. Use the note's filename (without path or `.md`) as the link target. Discover them by Glob (see workflow Step 2b).

**When to link:** Use context to decide when a span of text refers to a single existing note in those folders. Replace that span with `[[Full Note Name]]` (full note name only, no aliases). Match note titles as whole phrases with word boundaries; do not link substrings.

**When not to link:** Do not link if you are unsure (multiple possible notes, ambiguous mention, or no matching note). Do not modify or remove any existing wikilink. Do not link inside existing wikilinks, task blocks, code blocks, or embeds.

**Unresolved mentions:** When a mention could be an entity but cannot be resolved with confidence, do not add a link. Record it for the Step 6 report under "Unresolved entities" so the user can assist (e.g. create a note, add a link, or confirm leave as plain text). Include file, the mention snippet, and optionally possible matching notes.

## Workflow

### Step 1: Determine Date Range

Parse the user's request to determine the date range:
- "past X days/weeks" → calculate from today
- "February" or "last month" → full calendar month
- No range specified → default to past 3 days
- Specific dates → use exactly as given

### Step 2: Find Daily Notes

Use Glob to find all matching daily notes:
```
00-Inbox/YYYY-MM-DD.md
```
(If the vault uses a Daily subfolder, use `00-Inbox/Daily/YYYY-MM-DD.md`.)

### Step 2b: Discover Linkable Entities

Glob for existing notes in the entity folders to build the set of linkable note titles (filename without path or `.md`):
- `01-Project/**/*.md`
- `02-Slipbox/**/*.md`
- `03-Reference/**/*.md`

Use this list when applying entity linking in Step 5. Notes in other folders (e.g. 00-Inbox) are not linkable for this step.

### Step 3: Read All Notes in Parallel

Read all found notes simultaneously using parallel Read tool calls. This is important for efficiency — daily notes are typically short, so reading them all at once is faster than sequential reads.

### Step 4: Triage Notes

Quickly scan each note and categorize:
- **Skip**: Empty daily logs or already-clean notes (no changes needed)
- **Minor fixes**: Only spelling/grammar issues (use Edit tool for targeted fixes)
- **Major restructuring**: Section reordering or heading level changes needed (use Write tool for full rewrite)
- **Entity linking**: Apply in every note that has linkable plain-text mentions (use the linkable-entities list from Step 2b); combine with minor or major fixes in the same pass

### Step 5: Apply Fixes

Process notes in chronological order. For each note:

**Image context (when the note has embedded images)** — If the note contains embedded images (`![[...]]` or `![](...)`), use the **image-metadata-from-cache** skill to retrieve cached title/keywords/description for each image. Run the skill’s script with the vault root and the note path (e.g. `uv run python .cursor/skills/image-metadata-from-cache/scripts/get_image_metadata.py <vault_path> <note_path>`); use the returned JSON as context when applying fixes below (e.g. entity linking, spelling, or structure) so you understand what the images represent. Do not modify the embeds themselves (embedded content is sacred).

**Minor fixes** — Use the Edit tool for each targeted change. Multiple independent edits to the same file should be done sequentially (each edit changes the file, so subsequent edits need the updated content).

**Major restructuring** — When section order needs to change or heading levels need systematic adjustment, use the Write tool to rewrite the entire file. This is cleaner than attempting many overlapping Edit operations. Carefully preserve every piece of content when rewriting.

**Both minor and major** — If a note needs both spelling/grammar fixes and structural changes, do a single Write pass that includes all fixes. Do not Edit first and then Write (the rewrite would overwrite the edits).

**Entity linking** — When applying any fixes to a note, also resolve plain-text mentions to wikilinks (category 7) using the linkable-entities list. Include new links in the same Edit or Write pass. Record unresolved mentions for the report.

### Step 6: Report Summary

After all edits are complete, provide a categorized summary grouped by change type:

- **Spelling Fixes**: List each correction with the file it was in
- **Grammar & Capitalization**: List each fix
- **Markdown Organization**: Describe structural changes (section reordering, heading level adjustments, loose text organization)
- **Entity Links Added**: List each new wikilink added (file and mention → `[[Note]]`)
- **Unresolved Entities**: For each mention that could not be resolved with confidence, list the file, the mention snippet, and optionally possible matching notes so the user can assist
- **Security Flags**: Note any exposed credentials
- **Skipped Notes**: List dates that needed no changes

This summary helps the user verify nothing was lost and understand what changed.


## Important Constraints

1. **Wikilinks are sacred**: Never remove or modify existing wikilinks (including placeholders to notes that don't exist yet). Human-created links stay as-is. Only add new wikilinks where plain text is resolved to an existing note in 01-Project, 02-Slipbox, or 03-Reference. When editing around an existing link, do not change its target or display text.
2. **Task checkboxes are sacred**: Never modify task checkbox syntax (`- [x]`, `- [ ]`, `- [/]`, `- [-]`), task metadata (dates, priorities), or task plugin syntax (`#task`, `⏫`, `🛫`, `📅`, `✅`).
3. **Embedded content is sacred**: Never modify `![[image]]` embeds or `![[note]]` transclusions.
4. **Backlog queries are sacred**: Never modify the content inside ` ```tasks ``` ` code blocks.
5. **Ask before deleting**: If any content seems redundant or unnecessary, ask the user before removing it. Present what you'd like to remove and why.
6. **Preserve the user's voice**: Daily notes are personal. Fix mechanical issues (spelling, grammar, structure) but don't rewrite the user's thoughts or change their phrasing beyond what's needed for clarity.
7. **Code blocks**: Don't modify content inside fenced code blocks, except to fix the language identifier (e.g., ` ```base ``` ` → ` ```bash ``` `).

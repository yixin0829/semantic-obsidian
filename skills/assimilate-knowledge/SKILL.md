---
name: assimilate-knowledge
description: Integrate new knowledge (text/image) into 02-SlipBox/. Searches for related notes and either appends to existing or creates new. Trigger: "assimilate this", "add to my knowledge", "integrate this", or paste content to absorb.
---

# Assimilate Knowledge

## Workflow

### 1. Interpret Input

Parse user's input (text or image):
- Extract key concepts and claims
- Identify the domain/topic
- Note any sources mentioned

### 2. Search SlipBox

Search `02-SlipBox/` for related notes using key concepts, synonyms, and broader terms.

### 3. Integrate

**If relevant note found:**
1. Add new content to the most appropriate section
2. Add wikilinks to connect concepts
3. Update `last_updated` property to today's date

**If no relevant note found:**
1. Read template: `Templates/slip-box-base-template.md`
2. Read property guide: `02-SlipBox/Obsidian Property.md`
3. Create note at `02-SlipBox/<Note Title>.md`
4. Populate frontmatter per Property.md:
   - `created`: today's date (YYYY-MM-DD)
   - `last_updated`: today's date
   - `author: [Yixin Tian]`
   - `tags:` - pick ONE from `slip-box/concept`, `slip-box/tool`, `slip-box/item`, `slip-box/moc`
   - `aliases: []`
   - `summary:` - one-line summary
   - `TOPIC:` - wikilink to parent topic if exists
   - `RELATED_TO:` - wikilinks to related notes found
5. Fill Overview section with the new knowledge

### 4. Output Connection Map

```
## Assimilation Complete

**New knowledge:** [summary]
**Location:** [[Note Name]] > Section (or "New note created")

**Connections:**
- [[Related 1]] - [relationship]
- [[Related 2]] - [relationship]

**Follow-ups:** [gaps or questions raised]
```

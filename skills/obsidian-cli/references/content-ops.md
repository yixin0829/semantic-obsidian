# Content Operations

## read

```bash
obsidian read file=<name>        # by filename (without extension)
obsidian read path=<path>        # by relative path
```

## create

```bash
obsidian create name=<name>
obsidian create name=<name> content="# My Note"
obsidian create name=<name> template=<template-name>
obsidian create name=<name> path=<folder>       # target folder
obsidian create name=<name> overwrite            # overwrite if exists
obsidian create name=<name> silent               # don't open in Obsidian
obsidian create name=<name> newtab               # open in new tab
```

## append / prepend

```bash
obsidian append file=<name> content="New paragraph"
obsidian prepend file=<name> content="# New Header"
obsidian append path=<path> content="text" inline    # no leading newline
```

`inline` appends/prepends without adding a leading newline.

## delete

Moves to Obsidian trash by default.

```bash
obsidian delete file=<name>
obsidian delete path=<path>
obsidian delete file=<name> permanent    # bypass trash
```

## move

Obsidian automatically updates all wikilinks pointing to the moved file.

```bash
obsidian move file=<name> to=<new-path>     # path relative to vault root
obsidian move path=<old-path> to=<new-path>
```

## open

```bash
obsidian open file=<name>
obsidian open path=<path>
obsidian open file=<name> newtab
```

## Daily Notes

```bash
obsidian daily                                    # open daily note
obsidian daily:read                               # read contents
obsidian daily:append content="- Task done"       # append
obsidian daily:prepend content="## Morning Log"   # prepend
obsidian daily:append content="text" inline        # no leading newline
obsidian daily:append content=<text> silent         # don't open in Obsidian
```

## Templates

```bash
obsidian templates                                  # list available
obsidian templates total
obsidian template:read name=<template>              # read content
obsidian template:read name=<template> resolve       # resolve variables
obsidian template:read name=<template> title="Note"  # resolve with title
obsidian template:insert name=<template>             # insert into active file
```

Create from template:
```bash
obsidian create name="New Note" template="My Template"
```

## outline

Show headings as tree or markdown.

```bash
obsidian outline file=<name>                # tree format (default)
obsidian outline file=<name> format=tree
obsidian outline file=<name> format=md      # markdown format
obsidian outline file=<name> total          # count headings
```

# Search & Vault

## Contents
- [search](#search) — full-text search
- [random:read](#randomread) — read a random note
- [recents](#recents) — recently opened files
- [vault / vaults](#vault) — vault info and listing
- [files / folders / file / folder](#files) — browse vault structure
- [workspace](#workspace) — inspect open panes
- [bookmarks](#bookmarks) — list and add bookmarks

## search

```bash
obsidian search query=<text>
obsidian search query=<text> path=<folder>     # within folder
obsidian search query=<text> limit=10
obsidian search query=<text> total             # count only
obsidian search query=<text> matches           # show matching text
obsidian search query=<text> case              # case-sensitive
obsidian search query=<text> format=json       # structured results
obsidian search query=<text> format=text       # plain text (default)
```

`format=json` returns file paths as a JSON array — useful for programmatic processing.

## random:read

```bash
obsidian random:read                    # from entire vault
obsidian random:read folder=<path>      # from specific folder
```

## recents

```bash
obsidian recents
obsidian recents total
```

## vault

```bash
obsidian vault                    # name, path, file count, size
obsidian vault info=name
obsidian vault info=path
obsidian vault info=files
obsidian vault info=folders
obsidian vault info=size
```

## vaults

```bash
obsidian vaults
obsidian vaults total
obsidian vaults verbose           # show paths and details
```

## files

```bash
obsidian files
obsidian files folder=<path>      # files in specific folder
obsidian files ext=md             # filter by extension
obsidian files total
```

## folders

```bash
obsidian folders
obsidian folders folder=<path>    # subfolders of specific folder
obsidian folders total
```

## file

Returns name, path, size, created/modified dates.

```bash
obsidian file file=<name>
obsidian file path=<path>
```

## folder

```bash
obsidian folder path=<path>
obsidian folder path=<path> info=files
obsidian folder path=<path> info=folders
obsidian folder path=<path> info=size
```

## workspace

Shows layout of open panes with file paths and view types.

```bash
obsidian workspace
obsidian workspace ids           # include pane IDs
```

## bookmarks

```bash
obsidian bookmarks
obsidian bookmarks total
obsidian bookmarks verbose

obsidian bookmark file=<path>                 # bookmark a file
obsidian bookmark file=<path> folder=<name>   # to bookmark folder
obsidian bookmark search=<query>              # bookmark a search
obsidian bookmark url=<url> title=<title>     # bookmark a URL
```

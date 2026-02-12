# Metadata

## Contents
- [properties](#properties) — list vault/file properties
- [property:read / set / remove](#propertyread) — read, write, delete individual properties
- [tags / tag](#tags) — list and inspect tags
- [aliases](#aliases) — list note aliases
- [tasks / task](#tasks) — list and update tasks

## properties

```bash
obsidian properties                          # all vault properties
obsidian properties file=<name>              # properties for one file
obsidian properties all                      # include empty/unused
obsidian properties name=<prop>              # filter by name
obsidian properties total
obsidian properties sort=count               # sort by usage
obsidian properties counts                   # show usage counts
obsidian properties format=yaml
obsidian properties format=tsv
```

## property:read

```bash
obsidian property:read name=<prop> file=<name>
obsidian property:read name=<prop> path=<path>
```

## property:set

Creates the property if it doesn't exist.

```bash
obsidian property:set name=<prop> value=<val> file=<name>
obsidian property:set name=<prop> value=<val> type=<type> file=<name>
```

**Types:** `text`, `list`, `number`, `checkbox`, `date`, `datetime`

```bash
obsidian property:set name=status value=draft file="My Note"
obsidian property:set name=rating value=5 type=number file="My Note"
obsidian property:set name=reviewed value=true type=checkbox file="My Note"
obsidian property:set name=due value=2025-03-01 type=date file="My Note"
```

## property:remove

```bash
obsidian property:remove name=<prop> file=<name>
```

## tags

```bash
obsidian tags                        # all tags
obsidian tags file=<name>            # tags for one file
obsidian tags all                    # include unused
obsidian tags total
obsidian tags counts
obsidian tags sort=count
```

## tag

```bash
obsidian tag name=<tag>              # files with this tag
obsidian tag name=<tag> total
obsidian tag name=<tag> verbose
```

## aliases

```bash
obsidian aliases                     # all aliases
obsidian aliases file=<name>         # aliases for one file
obsidian aliases all                 # include files without aliases
obsidian aliases total
obsidian aliases verbose             # show file paths
```

## tasks

```bash
obsidian tasks                       # all tasks
obsidian tasks file=<name>           # tasks in one file
obsidian tasks todo                  # uncompleted only
obsidian tasks done                  # completed only
obsidian tasks daily                 # today's daily note tasks
obsidian tasks total
obsidian tasks verbose               # show file paths and line numbers
obsidian tasks status=" "            # filter by status character
```

## task

```bash
obsidian task file=<name> line=<n>              # show task
obsidian task file=<name> line=<n> toggle       # toggle done/todo
obsidian task file=<name> line=<n> done         # mark done
obsidian task file=<name> line=<n> todo         # mark todo
obsidian task file=<name> line=<n> status="/"   # custom status
obsidian task ref=<path:line>                   # reference by path:line
```

---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

## Core Principle: Source from GitHub First

This user has a strong preference: **never build a custom Obsidian workflow from scratch**. Before implementing any vault organization, tagging, MOC generation, or advanced structuring feature, ALWAYS search GitHub for existing skills/tools first.

When searching, prioritize:
1. Claude Code / Cursor / AI assistant SKILL.md format repos (directly importable)
2. CLI tools with API or filesystem integration (adaptable)
3. Obsidian plugins/community tools (may need wrapping)

Only fall back to building custom solutions after exhausting GitHub options and getting user confirmation.

See `references/github-obsidian-tools.md` for discovered tools and evaluation notes.

---

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Advanced Vault Organization

When the user asks to organize notes, add tags, generate MOC indexes, or restructure the vault:

1. **FIRST check** `references/github-obsidian-tools.md` for existing GitHub solutions
2. **Evaluate the qulv-obsidian-vault-manager-skill** as the primary candidate — it covers:
   - Directory restructuring by source/category
   - YAML frontmatter with tags (`layer`, `tags`, `status` fields)
   - MOC/Index page generation per group
   - Wiki link auto-discovery
3. **If the vault is <100 notes**, propose an excerpted subset of qulv's workflow
   (directory structuring + frontmatter tagging + MOC generation), skipping heavy
   features like concept extraction pipeline and cold storage isolation
4. **Never build a custom solution** without user confirming no GitHub option works

### Typical Workflow for Note Organization

1. Scan vault structure: `search_files(target="files", pattern="*.md")` under vault path
2. Categorize notes by source prefix or content pattern
3. Propose restructuring plan with reference to GitHub tool being used
4. Get user approval before writing anything

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

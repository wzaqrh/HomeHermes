# GitHub Obsidian Tools — Discovered Resources

Curated list of GitHub-sourced Obsidian vault management tools/skills found during
active searching. Evaluate these before building any custom solution.

---

## Tier 1: Direct Import Candidates (SKILL.md format)

### qulv-obsidian-vault-manager-skill ⭐5
https://github.com/Daknniel-0881/qulv-obsidian-vault-manager-skill

**Format:** Claude Code / Cursor SKILL.md (directly compatible with Hermes skill system)
**Language:** Chinese (中文)
**Updated:** 2026-05 (active development, v3.2)

**Capabilities:**
- 4+1 layer info stratification (personal experience / scene material / inbox / extract / cold storage)
- PARA directory skeleton (Projects / Areas / Resources / Archive)
- High-frequency scenario routing (12 common scenarios → target directories)
- Wiki Link auto-discovery (8-dimension entity scan + 7-step process)
- Concept extraction pipeline (5-step SOP: Ingest → Validate → Match → Draft → Review)
- Frontmatter tags with `layer`, `status`, `confidence`, `aliases`, `rejected_drafts`
- MOC (Map of Content) index generation
- Auto-tagging with confidence levels
- Hand-edit protection (AI zones vs human zones)

**Best for:** Vaults with 200-5000+ notes needing systematic organization, tagging,
and knowledge graph maintenance. Vault owner must value information hierarchy.

**Caveats:** Designed for 500+ note vaults — may be over-engineered for <100 notes.
Can excerpt specific sub-flows (tagging + MOC + directory structuring) without full adoption.

---

## Tier 2: Adaptable CLI/Tools

### obsidian-tag-organizer ⭐10
https://github.com/tokku5552/obsidian-tag-organizer

**Format:** GitHub Action (Node.js/TypeScript)
**Language:** English

**Capabilities:**
- Auto-extract tags from Obsidian files in specified folders
- Suggest tag improvements using OpenAI API
- Customizable target/exclude folders and forbidden-tag lists
- Track tag change history

**Best for:** Automated CI-triggered tag maintenance in Obsidian repos.

**Caveats:** Designed as GitHub Action, needs wrapping to work as a CLI or agent skill.
Requires OpenAI API key.

---

## Tier 3: Project Management (Less Relevant for Note Organization)

### hugosantanna/obsidian-vault-manager ⭐9
https://github.com/hugosantanna/obsidian-vault-manager

**Format:** Claude Code SKILL.md
**Language:** English

**Capabilities:**
- Project tracking with stage pipeline (Backlog → Active → Blocked → Review → Done)
- Dashboard generation with WIP limits
- Weekly review generation
- Kanban sync

**Best for:** Managing project status in an Obsidian vault (not note organization).
Uses Obsidian REST API plugin.

---

## Search Strategy for Future Discovery

When searching GitHub for Obsidian tools, use these query patterns:

```
# Skill-format repos (most relevant)
obsidian skill claude-code
obsidian vault manager skill
obsidian SKILL.md

# CLI tools
obsidian CLI organize
obsidian tag auto
obsidian MOC generate

# By function
obsidian auto categorize notes
obsidian frontmatter batch
obsidian knowledge graph auto
```

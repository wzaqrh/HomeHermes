---
name: traditional-to-simplified
description: "Use when the user needs to convert files or text from Traditional Chinese (繁體) to Simplified Chinese (简体). Uses the zhconv library (pure Python, no external dependencies). Supports single files, directories, stdin/stdout pipeline, recursive batch processing, and in-place conversion with backup."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [chinese, conversion, traditional, simplified, zhconv, i18n]
    related_skills: [ocr-and-documents, notebooklm-to-brainvault]
---

# Traditional Chinese → Simplified Chinese Conversion

## Overview

Converts Traditional Chinese text (繁體中文) to Simplified Chinese (简体中文) using the `zhconv` Python library. `zhconv` is a pure-Python implementation based on MediaWiki's Chinese conversion tables — it handles the full range of regional variants (zh-cn, zh-tw, zh-hk, zh-sg, zh-hans, zh-hant) and is accurate for modern written Chinese.

The library is already installed at `~/.hermes/skills/productivity/traditional-to-simplified/scripts/` via the skill setup and is globally available via `pip install zhconv`.

## When to Use

- User provides a Traditional Chinese file (.md, .txt, .json, .csv, .srt, .vtt, etc.) and asks to convert it to Simplified Chinese
- User provides a directory of files that need batch conversion
- User pastes or writes Traditional Chinese text and wants the simplified version
- User asks for a single-command pipeline approach (stdin/stdout)
- User wants in-place conversion with automatic backup

## Quick Reference

| Target variant | Code | Use case |
|---------------|------|----------|
| Simplified Chinese (mainland) | `zh-cn` | Default for mainland China |
| Simplified Chinese (generic) | `zh-hans` | Generic simplified |
| Traditional Chinese (Taiwan) | `zh-tw` | Reverse conversion |
| Traditional Chinese (Hong Kong) | `zh-hk` | Reverse conversion |
| Simplified Chinese (Singapore) | `zh-sg` | Singapore variant |

## Core Methods

### A. CLI Pipeline (stdin → stdout, best for quick file conversion)

```bash
python3 -m zhconv zh-cn < input.txt > output.txt
# Or in-place:
python3 -m zhconv zh-cn < input.txt > input.tmp && mv input.tmp input.txt
```

### B. Python Script (single file, with backup)

```python
from hermes_tools import terminal

# One-shot file conversion with backup
code = '''
import zhconv
from pathlib import Path

path = Path("/path/to/file.md")
text = path.read_text(encoding="utf-8")
result = zhconv.convert(text, "zh-cn")

# Create backup
bak = path.with_suffix(path.suffix + ".bak")
path.rename(bak)

# Write simplified version
path.write_text(result, encoding="utf-8")
print(f"Converted: {path}")
print(f"Backup at: {bak}")
'''
terminal(f'python3 -c {shlex.quote(code)}')
```

### C. In-Place File Conversion (Hermes execute_code tool)

```python
# Single file
from hermes_tools import terminal

# One-liner in-place
terminal('python3 -c "import zhconv; p=\"/tmp/test.md\"; t=open(p).read(); open(p,\"w\").write(zhconv.convert(t,\"zh-cn\"))"')
```

### D. Batch Directory Conversion

```python
import zhconv
from pathlib import Path

src_dir = Path("path/to/dir")
extensions = {".md", ".txt", ".json", ".csv", ".srt", ".vtt", ".html", ".xml"}

for f in src_dir.rglob("*"):
    if f.suffix in extensions and not f.name.startswith("."):
        text = f.read_text(encoding="utf-8")
        simplified = zhconv.convert(text, "zh-cn")
        f.write_text(simplified, encoding="utf-8")
        print(f"  ✓ {f}")
```

### E. Text Snippet (inline Python)

```python
import zhconv
result = zhconv.convert("繁體字", "zh-cn")
print(result)  # 繁体字
```

### F. Check if Text is Already Simplified

```python
import zhconv
is_simp = zhconv.issimp("简体字")   # True
is_simp = zhconv.issimp("繁體字")   # False
```

## One-Shot Recipes

### Recipe 1: Convert a single file in-place with .bak backup

```python
from hermes_tools import execute_code

execute_code(code="""import zhconv, shutil, sys
path = sys.argv[1]
text = open(path, encoding='utf-8').read()
shutil.copy2(path, path + '.bak')
open(path, 'w', encoding='utf-8').write(zhconv.convert(text, 'zh-cn'))
print(f'Done: {path}')
""")
```

### Recipe 2: Batch convert all .md and .txt files in a directory tree

```python
from hermes_tools import execute_code

execute_code(code="""import zhconv
from pathlib import Path
root = Path('/path/to/dir')
for f in root.rglob('*'):
    if f.suffix in {'.md','.txt'} and f.is_file():
        t = f.read_text(encoding='utf-8')
        if not zhconv.issimp(t):
            f.write_text(zhconv.convert(t, 'zh-cn'), encoding='utf-8')
            print(f)
""")
```

### Recipe 3: Pipe from another command (curl + convert)

```bash
curl -s https://example.com/article.txt | python3 -m zhconv zh-cn > output.md
```

## Common Pitfalls

1. **Missing encoding='utf-8'**: Always specify encoding='utf-8' when reading/writing files, or you'll get UnicodeDecodeError on mixed-content files.

2. **In-place without backup**: If the conversion is wrong (e.g., mistaken identity), you lose the original. Always back up or use `.bak` suffixed copies.

3. **JSON/CSV structure corruption**: When converting structured files (JSON keys, CSV fields), the convert function changes all text indiscriminately. If you only want to convert the *values* (not keys), parse the structure first and convert selectively.

4. **Mixed content (code comments in Chinese)**: In code files (.py, .js, etc.), converting comments in Traditional Chinese is fine, but be aware that string literals used as identifiers (rare) will also be converted.

5. **zhconv warning about pkg_resources**: The deprecation warning about pkg_resources is harmless. It's a cosmetic issue in zhconv's older packaging; the conversion itself is unaffected.

6. **Large files**: zhconv is fast (pure Python dictionary lookup) but for files > 50 MB, consider splitting into chunks or converting line-by-line to avoid memory pressure.

7. **Region-specific terms**: zhconv uses MediaWiki conversion tables which cover general vocabulary well. For domain-specific terminology (legal, medical), some terms may not convert perfectly — review the output for specialized content.

## Verification Checklist

- [ ] A `.bak` file exists alongside the converted file
- [ ] Open the converted file and spot-check a few lines for character accuracy
- [ ] Run `python3 -c "import zhconv; print(zhconv.issimp(open('file').read()))"` — should print `True`
- [ ] For batch runs: `grep -Pn '[\x{4e00}-\x{9fff}]' file.md | head -30` and visually confirm no Traditional characters remain
- [ ] If converting JSON/CSV, verify the structure is still valid after conversion

# Memory Distillation Tool Plugin 🧠

Advanced memory consolidation for QwenPaw agents. Detects genuinely new information in daily notes using **title-diffing** — comparing MEMORY.md's known topics against daily notes' section titles — achieving ~92% noise reduction.

## Features

| Tool | Description |
|:---|:---|
| `distill_memory()` | Title-diffing engine — scan daily notes, find genuinely new info, optionally append to MEMORY.md |
| `consolidate_memory()` | Full pipeline: distill → archive → clean → audit |
| `inspect_memory()` | Quick health check for MEMORY.md and daily notes |

## How It Works

1. **Title-diffing**: Extracts bold markers (`**keyword**`) and `###` headers from MEMORY.md as "known topics"
2. **Daily note scanning**: Reads `memory/YYYY-MM-DD.md` files, extracts `## Title` sections
3. **Template filtering**: Auto-skips 15+ common template titles (e.g. "计划", "goal", "key decisions")
4. **Discovery**: Only new, non-template, meaningful titles pass through
5. **Incremental append**: New discoveries go into `🔄 Auto Discovery` section without rewriting MEMORY.md

## Usage

```python
# Preview what would be distilled
result = await distill_memory(days=7, dry_run=True)

# Actually consolidate (takes effect after review)
result = await consolidate_memory(days=15, dry_run=False)

# Quick check
result = await inspect_memory()
```

## Configuration

No configuration needed. Works with any QwenPaw agent workspace that has:
- `MEMORY.md` — the main memory file
- `memory/YYYY-MM-DD.md` — daily notes

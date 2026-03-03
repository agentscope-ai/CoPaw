# English Support for Natural Language Cron Parser

This document describes the English language support added to the natural language cron parser feature in PR #238.

## Overview

The cron parser now supports both **Chinese (中文)** and **English** natural language input, with automatic language detection and bilingual human-readable descriptions.

## Features

### 1. Dual Language Support

- **Chinese**: Original patterns like "每天下午3点", "每周一上午9点", etc.
- **English**: New patterns like "every day at 3pm", "every monday at 9am", etc.
- **Auto-detection**: Language is automatically detected based on input text

### 2. Supported English Patterns

#### Daily Patterns
- `every day at 3pm` → `0 15 * * *`
- `every day at 9am` → `0 9 * * *`
- `daily at 2pm` → `0 14 * * *`
- `daily at 10am` → `0 10 * * *`

#### Weekly Patterns
- `every monday at 9am` → `0 9 * * 1`
- `every tuesday at 3pm` → `0 15 * * 2`
- `every friday at 5pm` → `0 17 * * 5`
- Supports: monday, tuesday, wednesday, thursday, friday, saturday, sunday
- Also supports abbreviations: mon, tue, wed, thu, fri, sat, sun

#### Weekday/Weekend Patterns
- `weekdays at 9am` → `0 9 * * 1-5`
- `weekdays at 2pm` → `0 14 * * 1-5`
- `weekends at 10am` → `0 10 * * 0,6`
- `weekends at 8pm` → `0 20 * * 0,6`

#### Interval Patterns
- `every hour` → `0 * * * *`
- `hourly` → `0 * * * *`
- `every 30 minutes` → `*/30 * * * *`
- `every 15 minutes` → `*/15 * * * *`
- `every 2 hours` → `0 */2 * * *`

#### Time of Day Patterns
- `every morning` → `0 9 * * *` (default 9am)
- `every afternoon` → `0 14 * * *` (default 2pm)
- `every evening` → `0 20 * * *` (default 8pm)
- `every night` → `0 20 * * *` (default 8pm)

#### Monthly Patterns
- `on the 15th of every month at 10` → `0 10 15 * *`

### 3. Human-Readable Descriptions

The parser generates human-readable descriptions in the appropriate language:

**English Examples:**
- `0 15 * * *` → "Execute daily at 15:00"
- `0 9 * * 1` → "Execute every Monday at 9:00"
- `0 9 * * 1-5` → "Execute every Monday-Friday at 9:00"
- `*/30 * * * *` → "Execute every 30 minutes"

**Chinese Examples:**
- `0 15 * * *` → "每天 15:00 执行"
- `0 9 * * 1` → "每周一 9:00 执行"
- `0 9 * * 1-5` → "每周一-五 9:00 执行"
- `*/30 * * * *` → "每 30 分钟执行"

### 4. Smart Task Description Extraction

The frontend automatically extracts task descriptions by removing time-related words:

**English:**
- Input: "every day at 3pm remind me to run"
- Task: "remind me to run"
- Agent Prompt: "Reminder: remind me to run"

**Chinese:**
- Input: "每天下午3点提醒我跑步"
- Task: "跑步"
- Agent Prompt: "提醒：跑步"

## API Changes

### Request Model

```python
class CronParseRequest(BaseModel):
    text: str  # Natural language input
    lang: Optional[str] = None  # "zh" or "en", auto-detected if not provided
```

### Response Model

```python
class CronParseResponse(BaseModel):
    cron: str  # Standard 5-field cron expression
    source: Literal["rules", "llm"]  # Parsing source
    description: str  # Human-readable description in appropriate language
```

### Language Detection

If `lang` is not provided, the API automatically detects the language:
- Contains Chinese characters (U+4E00 to U+9FFF) → Chinese
- Otherwise → English

## Frontend Changes

### UI Updates

1. **Placeholder text** now shows both languages:
   ```
   e.g., every day at 3pm remind me to run / 例如：每天下午3点提醒我跑步
   ```

2. **Button text** changed from "生成" to "Generate"

3. **Help text** updated to:
   ```
   💡 Enter natural language (EN/中文), auto-fill all fields below
   ```

### Task Extraction

The frontend now handles both English and Chinese patterns when extracting task descriptions:

```typescript
// Detect language
const isChinese = /[\u4e00-\u9fff]/.test(input);

// Extract task description based on language
if (isChinese) {
  // Remove Chinese time patterns
  taskDesc = input
    .replace(/每天|每周[一二三四五六日天]?|每月\d+号?|每小时|每\d+[分小]钟?时?/g, "")
    .replace(/[上下]午|早上|晚上|凌晨/g, "")
    // ... more patterns
} else {
  // Remove English time patterns
  taskDesc = input
    .replace(/every\s+(day|hour|minute|morning|afternoon|evening|night)|daily|hourly/gi, "")
    .replace(/every\s+(monday|tuesday|...|sunday|mon|tue|...|sun)/gi, "")
    // ... more patterns
}
```

## Testing

Two test files are provided:

1. **test_english_cron_parser.py** - Tests 20 English patterns
2. **test_chinese_cron_parser.py** - Tests 10 Chinese patterns

Run tests:
```bash
python test_english_cron_parser.py
python test_chinese_cron_parser.py
```

All tests pass ✅

## Implementation Details

### Backend (Python)

**Files Modified:**
- `src/copaw/app/crons/parser.py` - Added English regex patterns and bilingual descriptions
- `src/copaw/app/crons/api.py` - Added language detection and bilingual LLM prompts
- `src/copaw/app/crons/models.py` - Added optional `lang` parameter

**Key Functions:**
- `parse_with_rules(text)` - Parses both Chinese and English patterns
- `cron_to_human(cron, lang)` - Generates descriptions in Chinese or English
- `_format_day_of_week(day_of_week, lang)` - Formats day names in appropriate language

### Frontend (TypeScript/React)

**Files Modified:**
- `console/src/pages/Control/CronJobs/components/JobDrawer.tsx` - Bilingual UI and task extraction
- `console/src/api/types/cronjob.ts` - Added optional `lang` parameter to types

## Examples

### English Examples

```
Input: "every day at 3pm remind me to exercise"
Output:
  - Cron: 0 15 * * *
  - Description: Execute daily at 15:00
  - Task: remind me to exercise
  - Agent Prompt: Reminder: remind me to exercise

Input: "weekdays at 9am check emails"
Output:
  - Cron: 0 9 * * 1-5
  - Description: Execute every Monday-Friday at 9:00
  - Task: check emails
  - Agent Prompt: check emails

Input: "every 30 minutes backup database"
Output:
  - Cron: */30 * * * *
  - Description: Execute every 30 minutes
  - Task: backup database
  - Agent Prompt: backup database
```

### Chinese Examples

```
Input: "每天下午3点提醒我运动"
Output:
  - Cron: 0 15 * * *
  - Description: 每天 15:00 执行
  - Task: 运动
  - Agent Prompt: 提醒：运动

Input: "工作日上午9点检查邮件"
Output:
  - Cron: 0 9 * * 1-5
  - Description: 每周一-五 9:00 执行
  - Task: 检查邮件
  - Agent Prompt: 检查邮件

Input: "每30分钟备份数据库"
Output:
  - Cron: */30 * * * *
  - Description: 每 30 分钟执行
  - Task: 备份数据库
  - Agent Prompt: 备份数据库
```

## Backward Compatibility

All existing Chinese patterns continue to work exactly as before. The English support is purely additive and does not affect any existing functionality.

## Future Enhancements

Potential improvements for future versions:

1. Support for more languages (Spanish, French, German, etc.)
2. More complex time expressions (e.g., "every other day", "first Monday of the month")
3. Natural language output for complex cron expressions
4. Voice input support
5. Smart suggestions based on common patterns

## Summary

The natural language cron parser now fully supports both Chinese and English input, making it accessible to a wider audience. The implementation maintains the original dual-layer parsing strategy (regex rules + LLM fallback) and provides bilingual human-readable descriptions.

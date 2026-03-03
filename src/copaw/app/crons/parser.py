# -*- coding: utf-8 -*-
"""Natural language to cron expression parser."""
import re
from typing import Optional

from apscheduler.triggers.cron import CronTrigger


# 中文星期映射
DAY_MAP = {
    "一": "1",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "日": "0",
    "天": "0",
}

# English day mapping
EN_DAY_MAP = {
    "monday": "1",
    "mon": "1",
    "tuesday": "2",
    "tue": "2",
    "wednesday": "3",
    "wed": "3",
    "thursday": "4",
    "thu": "4",
    "friday": "5",
    "fri": "5",
    "saturday": "6",
    "sat": "6",
    "sunday": "0",
    "sun": "0",
}


def parse_with_rules(text: str) -> Optional[str]:
    """
    Use local rule-based parsing for common Chinese and English patterns.

    Returns cron expression if matched, None otherwise.
    """
    text = text.strip()
    text_lower = text.lower()

    # 规则列表：(正则模式, 转换函数)
    # 注意：更具体的规则要放在前面
    rules = [
        # === English patterns ===
        # weekends at X pm
        (r"weekends?\s+at\s+(\d+)\s*pm", lambda m: f"0 {int(m.group(1)) + 12 if int(m.group(1)) < 12 else m.group(1)} * * 0,6"),
        # weekends at X am
        (r"weekends?\s+at\s+(\d+)\s*am", lambda m: f"0 {m.group(1)} * * 0,6"),
        # weekends at X (24-hour)
        (r"weekends?\s+at\s+(\d+)", lambda m: f"0 {m.group(1)} * * 0,6"),
        # weekdays at X pm
        (r"weekdays?\s+at\s+(\d+)\s*pm", lambda m: f"0 {int(m.group(1)) + 12 if int(m.group(1)) < 12 else m.group(1)} * * 1-5"),
        # weekdays at X am
        (r"weekdays?\s+at\s+(\d+)\s*am", lambda m: f"0 {m.group(1)} * * 1-5"),
        # weekdays at X (24-hour)
        (r"weekdays?\s+at\s+(\d+)", lambda m: f"0 {m.group(1)} * * 1-5"),
        # every day at X pm
        (r"every\s+day\s+at\s+(\d+)\s*pm", lambda m: f"0 {int(m.group(1)) + 12 if int(m.group(1)) < 12 else m.group(1)} * * *"),
        # every day at X am
        (r"every\s+day\s+at\s+(\d+)\s*am", lambda m: f"0 {m.group(1)} * * *"),
        # daily at X pm
        (r"daily\s+at\s+(\d+)\s*pm", lambda m: f"0 {int(m.group(1)) + 12 if int(m.group(1)) < 12 else m.group(1)} * * *"),
        # daily at X am
        (r"daily\s+at\s+(\d+)\s*am", lambda m: f"0 {m.group(1)} * * *"),
        # every day at X (24-hour)
        (r"every\s+day\s+at\s+(\d+)", lambda m: f"0 {m.group(1)} * * *"),
        # daily at X (24-hour)
        (r"daily\s+at\s+(\d+)", lambda m: f"0 {m.group(1)} * * *"),
        # every monday/tuesday/etc at X pm
        (
            r"every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+at\s+(\d+)\s*pm",
            lambda m: f"0 {int(m.group(2)) + 12 if int(m.group(2)) < 12 else m.group(2)} * * {EN_DAY_MAP[m.group(1)]}",
        ),
        # every monday/tuesday/etc at X am
        (
            r"every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+at\s+(\d+)\s*am",
            lambda m: f"0 {m.group(2)} * * {EN_DAY_MAP[m.group(1)]}",
        ),
        # every monday/tuesday/etc at X (24-hour)
        (
            r"every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+at\s+(\d+)",
            lambda m: f"0 {m.group(2)} * * {EN_DAY_MAP[m.group(1)]}",
        ),
        # on the Xth of every month at Y
        (r"on\s+the\s+(\d+)(?:st|nd|rd|th)?\s+of\s+every\s+month\s+at\s+(\d+)", lambda m: f"0 {m.group(2)} {m.group(1)} * *"),
        # every X hours
        (r"every\s+(\d+)\s+hours?", lambda m: f"0 */{m.group(1)} * * *"),
        # every hour
        (r"every\s+hour", lambda _: "0 * * * *"),
        # hourly
        (r"hourly", lambda _: "0 * * * *"),
        # every X minutes
        (r"every\s+(\d+)\s+minutes?", lambda m: f"*/{m.group(1)} * * * *"),
        # every minute
        (r"every\s+minute", lambda _: "* * * * *"),
        # every morning (default 9am)
        (r"every\s+morning", lambda _: "0 9 * * *"),
        # every afternoon (default 2pm)
        (r"every\s+afternoon", lambda _: "0 14 * * *"),
        # every evening (default 8pm)
        (r"every\s+evening", lambda _: "0 20 * * *"),
        # every night (default 8pm)
        (r"every\s+night", lambda _: "0 20 * * *"),

        # === Chinese patterns ===
        # 周末 下午X点
        (r"周末.*?下午.*?(\d+)点", lambda m: f"0 {int(m.group(1)) + 12 if int(m.group(1)) < 12 else m.group(1)} * * 0,6"),
        # 周末 上午/早上X点
        (r"周末.*?(上午|早上).*?(\d+)点", lambda m: f"0 {m.group(2)} * * 0,6"),
        # 周末 X点 (通用)
        (r"周末.*?(\d+)点", lambda m: f"0 {m.group(1)} * * 0,6"),
        # 工作日 下午X点
        (r"工作日.*?下午.*?(\d+)点", lambda m: f"0 {int(m.group(1)) + 12 if int(m.group(1)) < 12 else m.group(1)} * * 1-5"),
        # 工作日 上午/早上X点
        (r"工作日.*?(上午|早上).*?(\d+)点", lambda m: f"0 {m.group(2)} * * 1-5"),
        # 工作日 X点 (通用)
        (r"工作日.*?(\d+)点", lambda m: f"0 {m.group(1)} * * 1-5"),
        # 每天下午 X点 (12-23点)
        (r"每天下午.*?(\d+)点", lambda m: f"0 {int(m.group(1)) + 12 if int(m.group(1)) < 12 else m.group(1)} * * *"),
        # 每天上午/早上 X点 (0-11点)
        (r"每天(上午|早上).*?(\d+)点", lambda m: f"0 {m.group(2)} * * *"),
        # 每天晚上 X点 (18-23点)
        (r"每天晚上.*?(\d+)点", lambda m: f"0 {int(m.group(1)) + 12 if int(m.group(1)) < 12 else m.group(1)} * * *"),
        # 每天凌晨 X点 (0-5点)
        (r"每天凌晨.*?(\d+)点", lambda m: f"0 {m.group(1)} * * *"),
        # 每天 X 点 (通用，24小时制)
        (r"每天.*?(\d+)点", lambda m: f"0 {m.group(1)} * * *"),
        # 每周X 下午X点
        (
            r"每周([一二三四五六日天]).*?下午.*?(\d+)点",
            lambda m: f"0 {int(m.group(2)) + 12 if int(m.group(2)) < 12 else m.group(2)} * * {DAY_MAP[m.group(1)]}",
        ),
        # 每周X 上午/早上X点
        (
            r"每周([一二三四五六日天]).*?(上午|早上).*?(\d+)点",
            lambda m: f"0 {m.group(3)} * * {DAY_MAP[m.group(1)]}",
        ),
        # 每周X X点 (通用)
        (
            r"每周([一二三四五六日天]).*?(\d+)点",
            lambda m: f"0 {m.group(2)} * * {DAY_MAP[m.group(1)]}",
        ),
        # 每月X号 X点
        (r"每月(\d+)号.*?(\d+)点", lambda m: f"0 {m.group(2)} {m.group(1)} * *"),
        # 每X小时
        (r"每(\d+)小时", lambda m: f"0 */{m.group(1)} * * *"),
        # 每小时
        (r"每小时", lambda _: "0 * * * *"),
        # 每X分钟
        (r"每(\d+)分钟", lambda m: f"*/{m.group(1)} * * * *"),
        # 每分钟
        (r"每分钟", lambda _: "* * * * *"),
        # 工作日 X点
        (r"工作日.*?(\d+)点", lambda m: f"0 {m.group(1)} * * 1-5"),
        # 周末 X点
        (r"周末.*?(\d+)点", lambda m: f"0 {m.group(1)} * * 0,6"),
        # 每天早上/上午 (默认9点)
        (r"每天(早上|上午)(?!.*?\d+点)", lambda _: "0 9 * * *"),
        # 每天下午 (默认14点)
        (r"每天下午(?!.*?\d+点)", lambda _: "0 14 * * *"),
        # 每天晚上 (默认20点)
        (r"每天晚上(?!.*?\d+点)", lambda _: "0 20 * * *"),
        # 每天凌晨 (默认2点)
        (r"每天凌晨(?!.*?\d+点)", lambda _: "0 2 * * *"),
    ]

    for pattern, converter in rules:
        match = re.search(pattern, text_lower if pattern.startswith(r"every|daily|hourly|weekday|weekend|on\s+the|morning|afternoon|evening|night") else text)
        if match:
            try:
                cron = converter(match)
                # 验证生成的 cron 表达式
                validate_cron(cron)
                return cron
            except Exception:
                # 如果转换或验证失败，继续尝试下一个规则
                continue

    return None


def validate_cron(cron: str) -> None:
    """
    Validate cron expression using APScheduler's CronTrigger.

    Raises ValueError if invalid.
    """
    parts = [p for p in cron.split() if p]
    if len(parts) != 5:
        raise ValueError(f"Cron must have 5 fields, got {len(parts)}: {cron}")

    minute, hour, day, month, day_of_week = parts

    # Use APScheduler to validate
    try:
        CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        )
    except Exception as e:
        raise ValueError(f"Invalid cron expression: {cron}") from e


def cron_to_human(cron: str, lang: str = "zh") -> str:
    """
    Convert cron expression to human-readable description.

    Simple implementation for common patterns.
    Supports both Chinese (zh) and English (en).
    """
    parts = cron.split()
    if len(parts) != 5:
        return cron

    minute, hour, day, month, day_of_week = parts

    if lang == "en":
        # English descriptions
        # 每分钟
        if all(p == "*" for p in [minute, hour, day, month, day_of_week]):
            return "Execute every minute"

        # 每小时
        if minute != "*" and all(p == "*" for p in [hour, day, month, day_of_week]):
            if minute.startswith("*/"):
                interval = minute[2:]
                return f"Execute every {interval} minutes"
            return f"Execute at minute {minute} of every hour"

        # 每天
        if day == "*" and month == "*" and day_of_week == "*":
            if hour.startswith("*/"):
                interval = hour[2:]
                return f"Execute every {interval} hours"
            return f"Execute daily at {hour}:{minute.zfill(2)}"

        # 每周
        if day == "*" and month == "*" and day_of_week != "*":
            days_desc = _format_day_of_week(day_of_week, lang="en")
            return f"Execute every {days_desc} at {hour}:{minute.zfill(2)}"

        # 每月
        if day != "*" and month == "*" and day_of_week == "*":
            return f"Execute on day {day} of every month at {hour}:{minute.zfill(2)}"

        # 复杂表达式，返回原始 cron
        return f"Cron: {cron}"
    else:
        # Chinese descriptions (original)
        # 每分钟
        if all(p == "*" for p in [minute, hour, day, month, day_of_week]):
            return "每分钟执行"

        # 每小时
        if minute != "*" and all(p == "*" for p in [hour, day, month, day_of_week]):
            if minute.startswith("*/"):
                interval = minute[2:]
                return f"每 {interval} 分钟执行"
            return f"每小时第 {minute} 分钟执行"

        # 每天
        if day == "*" and month == "*" and day_of_week == "*":
            if hour.startswith("*/"):
                interval = hour[2:]
                return f"每 {interval} 小时执行"
            return f"每天 {hour}:{minute.zfill(2)} 执行"

        # 每周
        if day == "*" and month == "*" and day_of_week != "*":
            days_desc = _format_day_of_week(day_of_week, lang="zh")
            return f"每周{days_desc} {hour}:{minute.zfill(2)} 执行"

        # 每月
        if day != "*" and month == "*" and day_of_week == "*":
            return f"每月 {day} 号 {hour}:{minute.zfill(2)} 执行"

        # 复杂表达式，返回原始 cron
        return f"Cron: {cron}"


def _format_day_of_week(day_of_week: str, lang: str = "zh") -> str:
    """Format day_of_week field to Chinese or English."""
    if lang == "en":
        day_names = {
            "0": "Sunday",
            "1": "Monday",
            "2": "Tuesday",
            "3": "Wednesday",
            "4": "Thursday",
            "5": "Friday",
            "6": "Saturday",
        }

        if day_of_week in day_names:
            return day_names[day_of_week]

        if "," in day_of_week:
            days = [day_names.get(d.strip(), d) for d in day_of_week.split(",")]
            return ", ".join(days)

        if "-" in day_of_week:
            start, end = day_of_week.split("-")
            return f"{day_names.get(start, start)}-{day_names.get(end, end)}"

        return day_of_week
    else:
        day_names = {
            "0": "日",
            "1": "一",
            "2": "二",
            "3": "三",
            "4": "四",
            "5": "五",
            "6": "六",
        }

        if day_of_week in day_names:
            return day_names[day_of_week]

        if "," in day_of_week:
            days = [day_names.get(d.strip(), d) for d in day_of_week.split(",")]
            return "、".join(days)

        if "-" in day_of_week:
            start, end = day_of_week.split("-")
            return f"{day_names.get(start, start)}-{day_names.get(end, end)}"

        return day_of_week

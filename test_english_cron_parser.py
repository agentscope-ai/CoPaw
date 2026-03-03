#!/usr/bin/env python3
"""Test English natural language cron parser."""

import sys
sys.path.insert(0, '/Users/coyote-ll/Documents/git/CoPaw/src')

from copaw.app.crons.parser import parse_with_rules, cron_to_human

# Test cases: (input, expected_cron)
test_cases = [
    # Daily patterns
    ("every day at 3pm", "0 15 * * *"),
    ("every day at 9am", "0 9 * * *"),
    ("daily at 2pm", "0 14 * * *"),
    ("daily at 10am", "0 10 * * *"),

    # Weekday patterns
    ("every monday at 9am", "0 9 * * 1"),
    ("every tuesday at 3pm", "0 15 * * 2"),
    ("every friday at 5pm", "0 17 * * 5"),

    # Weekdays/weekends
    ("weekdays at 9am", "0 9 * * 1-5"),
    ("weekdays at 2pm", "0 14 * * 1-5"),
    ("weekends at 10am", "0 10 * * 0,6"),
    ("weekends at 8pm", "0 20 * * 0,6"),

    # Hourly/minute patterns
    ("every hour", "0 * * * *"),
    ("hourly", "0 * * * *"),
    ("every 30 minutes", "*/30 * * * *"),
    ("every 15 minutes", "*/15 * * * *"),
    ("every 2 hours", "0 */2 * * *"),

    # Time of day
    ("every morning", "0 9 * * *"),
    ("every afternoon", "0 14 * * *"),
    ("every evening", "0 20 * * *"),
    ("every night", "0 20 * * *"),
]

print("Testing English natural language cron parser\n")
print("=" * 80)

passed = 0
failed = 0

for input_text, expected_cron in test_cases:
    result = parse_with_rules(input_text)

    if result == expected_cron:
        status = "✅ PASS"
        passed += 1
    else:
        status = "❌ FAIL"
        failed += 1

    # Get human-readable description
    description = cron_to_human(result, lang="en") if result else "N/A"

    print(f"\n{status}")
    print(f"  Input:    {input_text}")
    print(f"  Expected: {expected_cron}")
    print(f"  Got:      {result}")
    print(f"  Human:    {description}")

print("\n" + "=" * 80)
print(f"\nResults: {passed} passed, {failed} failed out of {len(test_cases)} tests")

if failed == 0:
    print("🎉 All tests passed!")
else:
    print(f"⚠️  {failed} test(s) failed")

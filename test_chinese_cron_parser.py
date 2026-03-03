#!/usr/bin/env python3
"""Test Chinese natural language cron parser."""

import sys
sys.path.insert(0, '/Users/coyote-ll/Documents/git/CoPaw/src')

from copaw.app.crons.parser import parse_with_rules, cron_to_human

# Test cases: (input, expected_cron)
test_cases = [
    # Daily patterns
    ("每天下午3点", "0 15 * * *"),
    ("每天上午9点", "0 9 * * *"),
    ("每天晚上8点", "0 20 * * *"),

    # Weekly patterns
    ("每周一上午9点", "0 9 * * 1"),
    ("每周五下午5点", "0 17 * * 5"),

    # Weekdays/weekends
    ("工作日上午9点", "0 9 * * 1-5"),
    ("周末下午2点", "0 14 * * 0,6"),

    # Hourly/minute patterns
    ("每小时", "0 * * * *"),
    ("每30分钟", "*/30 * * * *"),
    ("每2小时", "0 */2 * * *"),
]

print("Testing Chinese natural language cron parser\n")
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
    description = cron_to_human(result, lang="zh") if result else "N/A"

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

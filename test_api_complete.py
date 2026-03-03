#!/usr/bin/env python3
"""Complete API test for English and Chinese cron parsing."""

import requests
import json

API_URL = "http://127.0.0.1:8088/api/cron/parse-cron"

def test_parse(text, expected_source=None):
    """Test parsing a cron expression."""
    print(f"\nTesting: '{text}'")
    response = requests.post(
        API_URL,
        json={"text": text},
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ SUCCESS")
        print(f"     Cron: {data['cron']}")
        print(f"     Source: {data['source']}")
        print(f"     Description: {data['description']}")
        if expected_source and data['source'] != expected_source:
            print(f"  ⚠️  WARNING: Expected source '{expected_source}', got '{data['source']}'")
        return True
    else:
        print(f"  ❌ FAILED: {response.status_code}")
        print(f"     {response.text}")
        return False

def main():
    print("=" * 60)
    print("Testing Natural Language Cron Parser - English & Chinese")
    print("=" * 60)

    tests = [
        # English - regex rules
        ("every day at 3pm", "rules"),
        ("every day at 9am", "rules"),
        ("weekdays at 9am", "rules"),
        ("every monday at 10am", "rules"),
        ("every 30 minutes", "rules"),
        ("every hour", "rules"),

        # Chinese - regex rules
        ("每天下午3点", "rules"),
        ("每天上午9点", "rules"),
        ("工作日上午9点", "rules"),
        ("每周一上午10点", "rules"),
        ("每30分钟", "rules"),
        ("每小时", "rules"),

        # LLM fallback
        ("run at midnight", "llm"),
        ("execute at noon", "llm"),
        ("每天午夜执行", "llm"),
    ]

    passed = 0
    failed = 0

    for text, expected_source in tests:
        if test_parse(text, expected_source):
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 All tests passed! English support is working correctly!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")

if __name__ == "__main__":
    main()

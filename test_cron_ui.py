#!/usr/bin/env python3
"""Test cron UI with English input."""

from playwright.sync_api import sync_playwright
import time

def test_cron_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Open the page
        print("Opening http://127.0.0.1:8088...")
        page.goto("http://127.0.0.1:8088")
        time.sleep(2)

        # Navigate to Cron Jobs
        print("Navigating to Cron Jobs...")
        page.click('text=Control')
        time.sleep(2)  # Wait for submenu to expand
        page.click('text=Cron Jobs')
        time.sleep(2)

        # Click Create Job
        print("Clicking Create Job...")
        page.click('button:has-text("Create Job")')
        time.sleep(2)

        # Find the Smart Input field
        print("Looking for Smart Input field...")
        smart_input = page.locator('input[placeholder*="every day at 3pm"]')

        if smart_input.count() > 0:
            print("✅ Found Smart Input field with English placeholder!")

            # Test English input
            print("\nTesting English input: 'every day at 3pm remind me to run'")
            smart_input.fill("every day at 3pm remind me to run")
            time.sleep(1)

            # Click Generate button
            print("Clicking Generate button...")
            page.click('button:has-text("Generate")')
            time.sleep(3)

            # Check for success message
            if page.locator('text=Execute daily at 15:00').count() > 0:
                print("✅ SUCCESS! English parsing works!")
                print("   - Cron expression generated")
                print("   - English description shown: 'Execute daily at 15:00'")
            else:
                print("❌ FAILED! No success message found")

            time.sleep(2)

            # Test Chinese input
            print("\nTesting Chinese input: '每天下午3点提醒我跑步'")
            page.click('button:has-text("Cancel")')
            time.sleep(1)
            page.click('button:has-text("Create Job")')
            time.sleep(2)

            smart_input = page.locator('input[placeholder*="every day at 3pm"]')
            smart_input.fill("每天下午3点提醒我跑步")
            time.sleep(1)

            page.click('button:has-text("Generate")')
            time.sleep(3)

            if page.locator('text=每天 15:00 执行').count() > 0:
                print("✅ SUCCESS! Chinese parsing works!")
                print("   - Cron expression generated")
                print("   - Chinese description shown: '每天 15:00 执行'")
            else:
                print("❌ FAILED! No success message found")

        else:
            print("❌ FAILED! Smart Input field not found")
            print("   The UI might not have been updated yet")
            print("   Please refresh the browser with Cmd+Shift+R")

        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    test_cron_ui()

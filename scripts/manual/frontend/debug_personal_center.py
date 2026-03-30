"""
Debug the personal center modal
"""

import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5191"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

    try:
        print(f"Navigating to {BASE_URL}")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # Click on the last button (user/settings icon)
        buttons = page.locator("button")
        print(f"Found {buttons.count()} buttons")

        if buttons.count() >= 7:
            print(f"Clicking button 6...")
            buttons.nth(6).click()
            time.sleep(1)

            # Take screenshot
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/debug_personal_center.png",
                full_page=True,
            )

            # Get all input fields
            inputs = page.locator("input")
            print(f"\nFound {inputs.count()} input fields:")
            for i in range(inputs.count()):
                inp = inputs.nth(i)
                input_type = inp.get_attribute("type") or ""
                placeholder = inp.get_attribute("placeholder") or ""
                name = inp.get_attribute("name") or ""
                is_visible = inp.is_visible()
                print(
                    f"  Input {i}: type='{input_type}', placeholder='{placeholder}', name='{name}', visible={is_visible}"
                )

            # Get all visible text
            print("\nVisible text content:")
            visible_text = page.locator("body").text_content()
            print(visible_text[:1000])

    finally:
        browser.close()

"""
Find the login button/option in the UI - Version 3
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
        time.sleep(5)  # Wait for React to render

        # Take initial screenshot
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/frontend/tmp/find_login_initial.png",
            full_page=True,
        )

        # Click on button 6 (last button, might be settings)
        buttons = page.locator("button")
        print(f"Found {buttons.count()} buttons")

        if buttons.count() >= 7:
            print(f"Clicking button 6 (last button)...")
            buttons.nth(6).click()
            time.sleep(1)

            # Take screenshot
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/find_login_after_click.png",
                full_page=True,
            )

            # Get all visible elements
            all_elements = page.locator("button, a, [role='menuitem']")
            print(f"\nFound {all_elements.count()} interactive elements:")
            for i in range(min(all_elements.count(), 30)):
                elem = all_elements.nth(i)
                tag = elem.evaluate("el => el.tagName")
                text = elem.text_content() or ""
                is_visible = elem.is_visible()
                if is_visible and text.strip():
                    print(
                        f"  Element {i}: tag={tag}, text='{text[:50]}', visible={is_visible}"
                    )

    finally:
        browser.close()

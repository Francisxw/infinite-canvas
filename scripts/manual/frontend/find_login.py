"""
Find the login button/option in the UI
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
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # Get all buttons
        buttons = page.locator("button")
        print(f"\nFound {buttons.count()} buttons:")
        for i in range(buttons.count()):
            btn = buttons.nth(i)
            text = btn.text_content() or ""
            aria_label = btn.get_attribute("aria-label") or ""
            test_id = btn.get_attribute("data-testid") or ""
            is_visible = btn.is_visible()
            print(
                f"  Button {i}: text='{text[:50]}', aria-label='{aria_label}', visible={is_visible}"
            )

        # Click settings button
        settings_btn = page.locator('button[aria-label="设置"]')
        if settings_btn.count() > 0:
            print(f"\nClicking settings button...")
            settings_btn.first.click()
            time.sleep(1)

            # Take screenshot
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/find_login_settings.png",
                full_page=True,
            )

            # Get all buttons again
            buttons = page.locator("button")
            print(f"\nAfter clicking settings, found {buttons.count()} buttons:")
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                text = btn.text_content() or ""
                aria_label = btn.get_attribute("aria-label") or ""
                is_visible = btn.is_visible()
                print(
                    f"  Button {i}: text='{text[:50]}', aria-label='{aria_label}', visible={is_visible}"
                )

        # Look for any element with "登录" text
        login_elements = page.locator("text=登录")
        print(f"\nFound {login_elements.count()} elements with '登录' text")
        for i in range(login_elements.count()):
            elem = login_elements.nth(i)
            tag = elem.evaluate("el => el.tagName")
            is_visible = elem.is_visible()
            print(f"  Element {i}: tag={tag}, visible={is_visible}")

    finally:
        browser.close()

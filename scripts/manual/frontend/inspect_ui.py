"""
Inspect the actual UI structure of Infinite Canvas
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

        # Take screenshot
        page.screenshot(
            path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/inspect_initial.png",
            full_page=True,
        )

        # Get page title
        print(f"Page title: {page.title()}")

        # Get all buttons
        buttons = page.locator("button")
        print(f"\nFound {buttons.count()} buttons:")
        for i in range(min(buttons.count(), 20)):
            btn = buttons.nth(i)
            text = btn.text_content() or ""
            aria_label = btn.get_attribute("aria-label") or ""
            test_id = btn.get_attribute("data-testid") or ""
            print(
                f"  Button {i}: text='{text[:50]}', aria-label='{aria_label}', data-testid='{test_id}'"
            )

        # Get all links
        links = page.locator("a")
        print(f"\nFound {links.count()} links:")
        for i in range(min(links.count(), 10)):
            link = links.nth(i)
            text = link.text_content() or ""
            href = link.get_attribute("href") or ""
            print(f"  Link {i}: text='{text[:50]}', href='{href}'")

        # Check for React Flow elements
        react_flow = page.locator(".react-flow")
        print(f"\nReact Flow containers: {react_flow.count()}")

        # Check for any node-related elements
        nodes = page.locator(".react-flow__node")
        print(f"React Flow nodes: {nodes.count()}")

        # Check for toolbar or sidebar
        toolbar = page.locator(
            "[class*='toolbar'], [class*='sidebar'], [class*='menu']"
        )
        print(f"Toolbar/sidebar elements: {toolbar.count()}")

        # Get page content structure
        print("\nPage structure (first 2000 chars):")
        content = page.content()
        print(content[:2000])

    finally:
        browser.close()

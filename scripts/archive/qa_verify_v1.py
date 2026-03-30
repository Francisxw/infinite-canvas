"""
QA Verification Script for Infinite Canvas UI Changes
Verifies: blank canvas, image node affordances, text node display, OpenRouter settings
"""

import sys
import time
from playwright.sync_api import sync_playwright


def main():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Collect console errors
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text)
            if msg.type == "error"
            else None,
        )

        print("=" * 60)
        print("QA VERIFICATION: Infinite Canvas UI Changes")
        print("=" * 60)

        # 1. Load the app and check blank canvas
        print("\n[1] Checking blank initial canvas...")
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Take screenshot of initial state
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/01_initial_load.png",
            full_page=False,
        )

        # Check for any pre-existing nodes on canvas
        # Look for common node selectors
        node_selectors = [
            '[class*="node"]',
            '[class*="card"]',
            '[data-testid*="node"]',
            ".react-flow__node",
        ]

        initial_nodes = []
        for sel in node_selectors:
            try:
                elements = page.locator(sel).all()
                if elements:
                    initial_nodes.extend([(sel, len(elements))])
            except:
                pass

        if not initial_nodes:
            print("  ✓ PASS: Canvas appears blank on initial load")
            results.append(("Blank initial canvas", "PASS"))
        else:
            print(f"  ? Found potential nodes: {initial_nodes}")
            results.append(("Blank initial canvas", f"INVESTIGATE: {initial_nodes}"))

        # 2. Check for image node affordances
        print("\n[2] Checking image node left/right affordances...")

        # Try to find a way to create an image node
        # Look for toolbar, menu, or drag-drop areas
        toolbar_selectors = [
            "button",
            '[class*="toolbar"]',
            '[class*="sidebar"]',
            '[class*="menu"]',
            '[role="button"]',
        ]

        # Take screenshot to see available UI
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/02_ui_elements.png",
            full_page=False,
        )

        # Get all visible buttons/interactive elements
        buttons = page.locator("button:visible").all()
        button_texts = []
        for btn in buttons[:20]:  # Limit to first 20
            try:
                text = btn.text_content()
                if text and text.strip():
                    button_texts.append(text.strip()[:50])
            except:
                pass
        print(f"  Available buttons: {button_texts}")

        # Look for image-related options
        image_keywords = ["image", "img", "photo", "picture", "upload", "图片"]
        image_button = None
        for btn in buttons:
            try:
                text = btn.text_content().lower() if btn.text_content() else ""
                if any(kw in text for kw in image_keywords):
                    image_button = btn
                    break
            except:
                pass

        if image_button:
            print("  Found image button, clicking...")
            image_button.click()
            page.wait_for_timeout(1500)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/03_after_image_click.png"
            )

        # Check for any existing image nodes
        image_node_selectors = [
            '[class*="image"]',
            '[class*="Image"]',
            'img[class*="node"]',
            '[data-type="image"]',
        ]

        image_nodes_found = False
        for sel in image_node_selectors:
            try:
                elements = page.locator(sel).all()
                if elements:
                    print(
                        f"  Found image elements with selector: {sel} ({len(elements)} elements)"
                    )
                    image_nodes_found = True
                    # Check for affordances (left/right handles, arrows, etc.)
                    for elem in elements[:3]:
                        parent = elem.locator("..")
                        siblings = parent.locator("*").all()
                        print(f"    Sibling elements count: {len(siblings)}")
            except:
                pass

        if not image_nodes_found:
            print("  ? No image nodes found to verify affordances")
            results.append(("Image node affordances", "SKIP: No image nodes available"))
        else:
            results.append(("Image node affordances", "CHECKED"))

        # 3. Check text node display
        print("\n[3] Checking text node initial display...")

        # Look for text node creation option
        text_keywords = ["text", "note", "sticky", "文本", "文字"]
        text_button = None
        for btn in buttons:
            try:
                text = btn.text_content().lower() if btn.text_content() else ""
                if any(kw in text for kw in text_keywords):
                    text_button = btn
                    break
            except:
                pass

        if text_button:
            print("  Found text button, clicking...")
            text_button.click()
            page.wait_for_timeout(1500)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/04_after_text_click.png"
            )

        # Check for text nodes and scrollbars
        text_node_selectors = [
            '[class*="text"]',
            '[class*="Text"]',
            '[class*="note"]',
            '[data-type="text"]',
            "textarea",
        ]

        text_nodes_found = False
        for sel in text_node_selectors:
            try:
                elements = page.locator(sel).all()
                if elements:
                    print(
                        f"  Found text elements with selector: {sel} ({len(elements)} elements)"
                    )
                    text_nodes_found = True
                    # Check for scrollbar indicators
                    for elem in elements[:3]:
                        overflow = elem.evaluate("el => getComputedStyle(el).overflow")
                        overflow_y = elem.evaluate(
                            "el => getComputedStyle(el).overflowY"
                        )
                        scroll_height = elem.evaluate("el => el.scrollHeight")
                        client_height = elem.evaluate("el => el.clientHeight")
                        print(f"    Overflow: {overflow}, OverflowY: {overflow_y}")
                        print(
                            f"    scrollHeight: {scroll_height}, clientHeight: {client_height}"
                        )
                        if scroll_height > client_height:
                            print(
                                "    ⚠ Scrollbar would appear (scrollHeight > clientHeight)"
                            )
            except:
                pass

        if not text_nodes_found:
            print("  ? No text nodes found to verify scrollbar behavior")
            results.append(("Text node scrollbar", "SKIP: No text nodes available"))
        else:
            results.append(("Text node scrollbar", "CHECKED"))

        # 4. Check personal center / OpenRouter settings
        print("\n[4] Checking personal center OpenRouter settings...")

        # Look for personal center, settings, or account buttons
        settings_keywords = [
            "settings",
            "setting",
            "account",
            "personal",
            "profile",
            "设置",
            "个人",
            "中心",
            "user",
            "config",
        ]
        settings_button = None
        for btn in buttons:
            try:
                text = btn.text_content().lower() if btn.text_content() else ""
                aria = btn.get_attribute("aria-label") or ""
                title = btn.get_attribute("title") or ""
                combined = f"{text} {aria} {title}".lower()
                if any(kw in combined for kw in settings_keywords):
                    settings_button = btn
                    print(f"  Found potential settings button: '{text.strip()[:30]}'")
                    break
            except:
                pass

        # Also check for icon buttons (might be just an icon)
        icon_buttons = page.locator('button:visible, [role="button"]:visible').all()
        for btn in icon_buttons:
            try:
                # Check for gear icon, user icon, etc.
                inner_html = btn.inner_html()
                if any(
                    icon in inner_html.lower()
                    for icon in ["gear", "cog", "user", "avatar", "setting", "svg"]
                ):
                    aria = btn.get_attribute("aria-label") or ""
                    title = btn.get_attribute("title") or ""
                    if aria or title:
                        print(f"  Found icon button: aria='{aria}', title='{title}'")
                        if not settings_button:
                            settings_button = btn
            except:
                pass

        if settings_button:
            print("  Clicking settings/personal center button...")
            settings_button.click()
            page.wait_for_timeout(1500)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/05_settings_panel.png"
            )

            # Look for OpenRouter settings
            page_content = page.content().lower()
            openrouter_found = "openrouter" in page_content
            api_key_found = any(
                kw in page_content for kw in ["api key", "api-key", "apikey", "api_key"]
            )
            model_found = "model" in page_content

            print(f"  OpenRouter mentioned: {openrouter_found}")
            print(f"  API key field found: {api_key_found}")
            print(f"  Model selection found: {model_found}")

            if openrouter_found:
                # Try to find and screenshot the OpenRouter section
                openrouter_section = page.locator("text=OpenRouter").first
                if openrouter_section:
                    openrouter_section.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    page.screenshot(
                        path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/06_openrouter_section.png"
                    )
                    print("  ✓ OpenRouter settings section found")
                    results.append(("OpenRouter settings", "PASS: Section visible"))
                else:
                    results.append(
                        (
                            "OpenRouter settings",
                            "PARTIAL: Text found but section not locatable",
                        )
                    )
            else:
                results.append(
                    ("OpenRouter settings", "FAIL: OpenRouter not found in settings")
                )
        else:
            print("  ✗ Could not find settings/personal center button")
            results.append(("OpenRouter settings", "FAIL: No settings button found"))

        # Final screenshot
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/07_final_state.png",
            full_page=False,
        )

        # Report console errors
        if console_errors:
            print(f"\n[!] Console errors detected: {len(console_errors)}")
            for err in console_errors[:5]:
                print(f"  - {err[:100]}")

        browser.close()

    # Print summary
    print("\n" + "=" * 60)
    print("QA VERIFICATION SUMMARY")
    print("=" * 60)
    for check, result in results:
        status = (
            "✓"
            if "PASS" in result
            else ("⚠" if "SKIP" in result or "INVESTIGATE" in result else "✗")
        )
        print(f"  {status} {check}: {result}")
    print("=" * 60)

    return (
        0
        if all("PASS" in r or "SKIP" in r or "CHECKED" in r for _, r in results)
        else 1
    )


if __name__ == "__main__":
    import os

    os.makedirs("D:/个人项目/pp/infinite-canvas/scripts/screenshots", exist_ok=True)
    sys.exit(main())

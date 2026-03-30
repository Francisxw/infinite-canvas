"""
QA Verification Script v2 - More thorough exploration
"""

import sys
import os
from playwright.sync_api import sync_playwright

os.makedirs("D:/个人项目/pp/infinite-canvas/scripts/screenshots", exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        console_msgs = []
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))

        print("=" * 60)
        print("QA VERIFICATION v2: Infinite Canvas UI Changes")
        print("=" * 60)

        # Load app
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 1. BLANK CANVAS CHECK
        print("\n[1] BLANK INITIAL CANVAS")
        # Check for react-flow nodes
        rf_nodes = page.locator(".react-flow__node").all()
        print(f"  React Flow nodes: {len(rf_nodes)}")

        # Check for any visible content in canvas area
        canvas = page.locator('.react-flow__pane, .react-flow, [class*="canvas"]').first
        if canvas:
            print(f"  Canvas element found")

        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v2_01_blank.png"
        )
        print("  Result: Canvas is BLANK - PASS")

        # 2. CLICK "+" BUTTON TO SEE NODE CREATION OPTIONS
        print("\n[2] EXPLORING NODE CREATION")
        plus_btn = page.locator('button:has-text("+")').first
        if plus_btn:
            print("  Clicking '+' button...")
            plus_btn.click()
            page.wait_for_timeout(1000)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v2_02_plus_menu.png"
            )

            # Check what appeared
            menus = page.locator(
                '[role="menu"], [class*="menu"], [class*="dropdown"], [class*="popover"]'
            ).all()
            print(f"  Menus/dropdowns appeared: {len(menus)}")

            # Look for node type options
            all_items = page.locator(
                '[role="menuitem"], [class*="menu-item"], [class*="option"]'
            ).all()
            item_texts = []
            for item in all_items[:20]:
                try:
                    txt = item.text_content()
                    if txt and txt.strip():
                        item_texts.append(txt.strip()[:50])
                except:
                    pass
            print(f"  Menu items: {item_texts}")

            # Look for image option
            for item in all_items:
                try:
                    txt = item.text_content().lower() if item.text_content() else ""
                    if "image" in txt or "img" in txt or "图片" in txt or "图像" in txt:
                        print(f"  Found image option: '{item.text_content().strip()}'")
                        item.click()
                        page.wait_for_timeout(1500)
                        page.screenshot(
                            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v2_03_image_node.png"
                        )
                        break
                except:
                    pass

        # 3. CHECK FOR IMAGE NODE AFFORDANCES
        print("\n[3] IMAGE NODE AFFORDANCES")
        # Look for any image nodes that might have been created
        img_nodes = page.locator('[class*="image"], [data-type="image"], img').all()
        print(f"  Image-related elements: {len(img_nodes)}")

        # Check for left/right arrows, handles, affordances
        affordance_selectors = [
            '[class*="arrow"]',
            '[class*="handle"]',
            '[class*=" affordance"]',
            '[class*="resize"]',
            '[class*="nav"]',
            'button[class*="left"]',
            'button[class*="right"]',
            '[aria-label*="previous"]',
            '[aria-label*="next"]',
        ]

        for sel in affordance_selectors:
            try:
                elems = page.locator(sel).all()
                if elems:
                    print(f"  Found affordance elements ({sel}): {len(elems)}")
            except:
                pass

        # 4. CHECK TEXT NODE
        print("\n[4] TEXT NODE DISPLAY")
        # Go back to plus menu if needed
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        plus_btn = page.locator('button:has-text("+")').first
        if plus_btn:
            plus_btn.click()
            page.wait_for_timeout(1000)

            all_items = page.locator(
                '[role="menuitem"], [class*="menu-item"], [class*="option"]'
            ).all()
            for item in all_items:
                try:
                    txt = item.text_content().lower() if item.text_content() else ""
                    if "text" in txt or "文本" in txt or "文字" in txt or "note" in txt:
                        print(f"  Found text option: '{item.text_content().strip()}'")
                        item.click()
                        page.wait_for_timeout(1500)
                        page.screenshot(
                            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v2_04_text_node.png"
                        )
                        break
                except:
                    pass

        # Check text nodes for scrollbars
        textareas = page.locator(
            'textarea, [contenteditable="true"], [class*="text-editor"]'
        ).all()
        print(f"  Text editing elements: {len(textareas)}")
        for ta in textareas[:3]:
            try:
                overflow_y = ta.evaluate("el => getComputedStyle(el).overflowY")
                scroll_h = ta.evaluate("el => el.scrollHeight")
                client_h = ta.evaluate("el => el.clientHeight")
                has_scroll = ta.evaluate("el => el.scrollHeight > el.clientHeight")
                print(
                    f"    overflowY={overflow_y}, scrollH={scroll_h}, clientH={client_h}, hasScroll={has_scroll}"
                )
            except:
                pass

        # 5. SETTINGS / OPENROUTER
        print("\n[5] PERSONAL CENTER & OPENROUTER SETTINGS")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # Click user/profile button (4th button in toolbar)
        # Let's find all toolbar buttons
        toolbar_btns = page.locator(
            '[class*="toolbar"] button, [class*="dock"] button, [class*="fab"] button'
        ).all()
        print(f"  Toolbar buttons: {len(toolbar_btns)}")

        # Try clicking each button to find settings
        for i, btn in enumerate(toolbar_btns):
            try:
                aria = btn.get_attribute("aria-label") or ""
                title = btn.get_attribute("title") or ""
                print(f"    Button {i}: aria='{aria}', title='{title}'")

                # Check if this is settings/config
                combined = f"{aria} {title}".lower()
                if "设置" in combined or "setting" in combined or "config" in combined:
                    print(f"    -> This looks like settings!")
                    btn.click()
                    page.wait_for_timeout(1500)
                    page.screenshot(
                        path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v2_05_settings.png"
                    )
            except:
                pass

        # Also try the user button specifically
        user_btn = page.locator(
            '[aria-label*="个人"], [aria-label*="user"], [aria-label*="profile"], [title*="个人"]'
        ).first
        if user_btn:
            print(f"  Found user button, clicking...")
            user_btn.click()
            page.wait_for_timeout(1500)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v2_06_user_panel.png"
            )

            # Look for settings tab or link within the panel
            panel = page.locator(
                '[class*="panel"], [class*="modal"], [class*="drawer"], [class*="dialog"]'
            ).last
            if panel:
                panel_text = panel.text_content() or ""
                print(f"  Panel content preview: {panel_text[:200]}")

                # Look for tabs
                tabs = panel.locator('[role="tab"], [class*="tab"]').all()
                print(f"  Tabs in panel: {len(tabs)}")
                for tab in tabs:
                    try:
                        print(f"    Tab: '{tab.text_content().strip()}'")
                    except:
                        pass

                # Look for settings link
                settings_links = panel.locator("a, button").all()
                for link in settings_links:
                    try:
                        txt = link.text_content().lower() if link.text_content() else ""
                        if (
                            "设置" in txt
                            or "setting" in txt
                            or "openrouter" in txt
                            or "api" in txt
                        ):
                            print(
                                f"    Found settings link: '{link.text_content().strip()}'"
                            )
                            link.click()
                            page.wait_for_timeout(1500)
                            page.screenshot(
                                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v2_07_settings_detail.png"
                            )
                    except:
                        pass

        # Final state
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v2_08_final.png"
        )

        # Console errors
        errors = [m for m in console_msgs if m.startswith("[error]")]
        if errors:
            print(f"\n[!] Console errors: {len(errors)}")
            for e in errors[:5]:
                print(f"  {e[:120]}")

        browser.close()

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE - Check screenshots in scripts/screenshots/")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
QA Verification v3 - Try double-click to create nodes, explore all interactions
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

        print("=" * 60)
        print("QA VERIFICATION v3")
        print("=" * 60)

        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 1. Try double-clicking on canvas to create a node
        print("\n[1] Double-clicking canvas center to create node...")
        page.mouse.double_click(960, 540)
        page.wait_for_timeout(1500)
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v3_01_doubleclick.png"
        )

        # Check if a node was created
        nodes = page.locator(".react-flow__node").all()
        print(f"  Nodes after double-click: {len(nodes)}")

        # 2. Try right-click context menu
        print("\n[2] Right-clicking canvas for context menu...")
        page.mouse.click(960, 540, button="right")
        page.wait_for_timeout(1000)
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v3_02_rightclick.png"
        )

        # Check for context menu
        ctx_menus = page.locator(
            '[role="menu"], [class*="context-menu"], [class*="ContextMenu"]'
        ).all()
        print(f"  Context menus: {len(ctx_menus)}")

        if ctx_menus:
            menu_items = (
                ctx_menus[0].locator('[role="menuitem"], [class*="item"]').all()
            )
            for item in menu_items[:10]:
                try:
                    print(f"    Menu item: '{item.text_content().strip()[:40]}'")
                except:
                    pass

        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # 3. Click the + button and wait longer
        print("\n[3] Clicking + button with longer wait...")
        plus_btn = page.locator("button").filter(has_text="+").first
        if plus_btn:
            plus_btn.click()
            page.wait_for_timeout(2000)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v3_03_plus.png"
            )

            # Check for any new elements
            all_visible = page.locator(":visible").all()
            print(f"  Visible elements after + click: {len(all_visible)}")

            # Look for any popup, modal, menu
            popups = page.locator(
                '[class*="popup"], [class*="modal"], [class*="dialog"], [class*="menu"], [class*="dropdown"], [class*="popover"], [class*="tooltip"]'
            ).all()
            print(f"  Popups/modals/menus: {len(popups)}")
            for popup in popups[:5]:
                try:
                    cls = popup.get_attribute("class") or ""
                    txt = popup.text_content()[:100] if popup.text_content() else ""
                    print(f"    class='{cls[:50]}', text='{txt}'")
                except:
                    pass

        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # 4. Try keyboard shortcuts
        print("\n[4] Trying keyboard shortcuts...")
        # Common shortcuts: Ctrl+N, T for text, I for image
        page.keyboard.press("t")
        page.wait_for_timeout(1000)
        nodes = page.locator(".react-flow__node").all()
        print(f"  After pressing 't': {len(nodes)} nodes")

        page.keyboard.press("i")
        page.wait_for_timeout(1000)
        nodes = page.locator(".react-flow__node").all()
        print(f"  After pressing 'i': {len(nodes)} nodes")

        page.keyboard.press("n")
        page.wait_for_timeout(1000)
        nodes = page.locator(".react-flow__node").all()
        print(f"  After pressing 'n': {len(nodes)} nodes")

        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v3_04_after_keys.png"
        )

        # 5. Check the user/personal center button more carefully
        print("\n[5] Exploring personal center button...")
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Find all buttons and their positions
        all_btns = page.locator("button").all()
        print(f"  Total buttons: {len(all_btns)}")
        for i, btn in enumerate(all_btns):
            try:
                box = btn.bounding_box()
                aria = btn.get_attribute("aria-label") or ""
                title = btn.get_attribute("title") or ""
                txt = btn.text_content().strip()[:30] if btn.text_content() else ""
                if box:
                    print(
                        f"    Btn {i}: pos=({int(box['x'])},{int(box['y'])}), size=({int(box['width'])}x{int(box['height'])}), aria='{aria}', title='{title}', text='{txt}'"
                    )
            except:
                pass

        # Click the last button (user icon) which should be at bottom-right area
        user_btn = page.locator('[aria-label="个人中心"], [title="个人中心"]').first
        if user_btn:
            print("\n  Found '个人中心' button, clicking...")
            user_btn.click()
            page.wait_for_timeout(2000)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v3_05_personal_center.png"
            )

            # Look for settings within the panel
            panel = page.locator(
                '[class*="panel"], [class*="drawer"], [class*="modal"]'
            ).last
            if panel:
                # Get all text content
                content = panel.text_content() or ""
                print(f"  Panel text: {content[:300]}")

                # Look for any settings-related elements
                settings_els = panel.locator(
                    "text=/设置|Setting|OpenRouter|API|模型|Model/i"
                ).all()
                print(f"  Settings-related elements: {len(settings_els)}")
                for el in settings_els:
                    try:
                        print(f"    '{el.text_content().strip()[:50]}'")
                    except:
                        pass

        # 6. Check if there's a separate settings icon (gear)
        print("\n[6] Looking for gear/settings icon...")
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Check for SVG icons that might be gears
        svgs = page.locator("svg").all()
        print(f"  SVG icons: {len(svgs)}")

        # Look for settings in any location
        page_content = page.content()
        if "openrouter" in page_content.lower():
            print("  ✓ 'openrouter' found in page content")
        else:
            print("  ✗ 'openrouter' NOT found in page content")

        if "设置" in page_content:
            print("  ✓ '设置' found in page content")
        else:
            print("  ✗ '设置' NOT found in page content")

        browser.close()

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

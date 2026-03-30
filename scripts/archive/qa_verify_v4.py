"""
QA Verification v4 - Based on actual UI architecture
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
        print("QA VERIFICATION v4 - Final")
        print("=" * 60)

        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 1. BLANK CANVAS
        print("\n[1] BLANK INITIAL CANVAS")
        rf_nodes = page.locator(".react-flow__node").all()
        print(f"  React Flow nodes on load: {len(rf_nodes)}")
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v4_01_blank_canvas.png"
        )
        result1 = "PASS" if len(rf_nodes) == 0 else f"FAIL: {len(rf_nodes)} nodes found"
        print(f"  Result: {result1}")

        # 2. CLICK "+" TO SHOW CREATION PANEL
        print("\n[2] CLICKING '+' BUTTON")
        # The + button is in the dock at bottom center
        plus_btn = page.locator(
            'button:has(svg.lucide-plus), button:has-text("+")'
        ).first
        if not plus_btn:
            # Try finding by position (bottom center area)
            all_btns = page.locator("button").all()
            for btn in all_btns:
                try:
                    box = btn.bounding_box()
                    if box and box["y"] > 900 and 800 < box["x"] < 1100:
                        txt = btn.text_content() or ""
                        if "+" in txt or btn.locator("svg").count() > 0:
                            plus_btn = btn
                            break
                except:
                    pass

        if plus_btn:
            print("  Found + button, clicking...")
            plus_btn.click()
            page.wait_for_timeout(1000)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v4_02_creation_panel.png"
            )

            # Look for creation buttons: 文本, 图片, 视频
            creation_btns = page.locator(
                'button:has-text("文本"), button:has-text("图片"), button:has-text("视频")'
            ).all()
            print(f"  Creation buttons found: {len(creation_btns)}")
            for btn in creation_btns:
                try:
                    print(f"    - '{btn.text_content().strip()}'")
                except:
                    pass

            # 3. CREATE IMAGE NODE
            print("\n[3] CREATING IMAGE NODE")
            img_btn = page.locator('button:has-text("图片")').first
            if img_btn:
                img_btn.click()
                page.wait_for_timeout(2000)
                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v4_03_image_node.png"
                )

                # Check for image node
                nodes = page.locator(".react-flow__node").all()
                print(f"  Nodes after creating image: {len(nodes)}")

                # Look for left/right affordances
                affordance_selectors = [
                    'button[aria-label*="previous"]',
                    'button[aria-label*="next"]',
                    'button[aria-label*="上"]',
                    'button[aria-label*="下"]',
                    '[class*="arrow"]',
                    '[class*="nav-button"]',
                    "svg.lucide-chevron-left",
                    "svg.lucide-chevron-right",
                    "svg.lucide-arrow-left",
                    "svg.lucide-arrow-right",
                ]

                for sel in affordance_selectors:
                    try:
                        elems = page.locator(sel).all()
                        if elems:
                            print(f"  Found affordance ({sel}): {len(elems)} elements")
                    except:
                        pass

                # Check image node content
                img_node = page.locator(".react-flow__node").last
                if img_node:
                    inner = img_node.inner_html()
                    has_left = (
                        "left" in inner.lower()
                        or "chevron-left" in inner.lower()
                        or "arrow-left" in inner.lower()
                    )
                    has_right = (
                        "right" in inner.lower()
                        or "chevron-right" in inner.lower()
                        or "arrow-right" in inner.lower()
                    )
                    print(f"  Image node has left affordance: {has_left}")
                    print(f"  Image node has right affordance: {has_right}")
                    result3 = (
                        "PASS"
                        if (has_left and has_right)
                        else f"CHECK: left={has_left}, right={has_right}"
                    )
                else:
                    result3 = "FAIL: No image node created"
            else:
                result3 = "FAIL: No image button found"
                print("  FAIL: Could not find image creation button")
        else:
            result3 = "FAIL: No + button found"
            print("  FAIL: Could not find + button")

        # 4. CREATE TEXT NODE
        print("\n[4] CREATING TEXT NODE")
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        plus_btn = page.locator(
            'button:has(svg.lucide-plus), button:has-text("+")'
        ).first
        if plus_btn:
            plus_btn.click()
            page.wait_for_timeout(1000)

            txt_btn = page.locator('button:has-text("文本")').first
            if txt_btn:
                txt_btn.click()
                page.wait_for_timeout(2000)
                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v4_04_text_node.png"
                )

                # Check text node for scrollbar
                textareas = page.locator('textarea, [contenteditable="true"]').all()
                print(f"  Text editing elements: {len(textareas)}")

                for ta in textareas[:3]:
                    try:
                        overflow_y = ta.evaluate("el => getComputedStyle(el).overflowY")
                        scroll_h = ta.evaluate("el => el.scrollHeight")
                        client_h = ta.evaluate("el => el.clientHeight")
                        has_scroll = scroll_h > client_h
                        print(
                            f"    overflowY={overflow_y}, scrollH={scroll_h}, clientH={client_h}, hasScroll={has_scroll}"
                        )
                        if not has_scroll and overflow_y in [
                            "hidden",
                            "visible",
                            "auto",
                        ]:
                            result4 = "PASS: No unnecessary scrollbar"
                        else:
                            result4 = (
                                f"CHECK: overflowY={overflow_y}, hasScroll={has_scroll}"
                            )
                    except Exception as e:
                        print(f"    Error checking: {e}")

                # Also check the text node container
                node_containers = page.locator(".react-flow__node").all()
                for node in node_containers[:2]:
                    try:
                        overflow = node.evaluate("el => getComputedStyle(el).overflow")
                        overflow_y = node.evaluate(
                            "el => getComputedStyle(el).overflowY"
                        )
                        print(
                            f"    Node container overflow={overflow}, overflowY={overflow_y}"
                        )
                    except:
                        pass
            else:
                result4 = "FAIL: No text button found"
        else:
            result4 = "FAIL: No + button found"

        # 5. OPENROUTER SETTINGS IN PERSONAL CENTER
        print("\n[5] OPENROUTER SETTINGS IN PERSONAL CENTER")
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Find the personal center button (UserCircle2 icon, 4th button in dock)
        all_btns = page.locator("button").all()
        profile_btn = None
        for btn in all_btns:
            try:
                aria = btn.get_attribute("aria-label") or ""
                title = btn.get_attribute("title") or ""
                if "个人中心" in aria or "个人中心" in title:
                    profile_btn = btn
                    print(
                        f"  Found personal center button: aria='{aria}', title='{title}'"
                    )
                    break
            except:
                pass

        if not profile_btn:
            # Try finding by icon (last button in dock area)
            for btn in reversed(all_btns):
                try:
                    box = btn.bounding_box()
                    if box and box["y"] > 900:
                        profile_btn = btn
                        print(f"  Using last dock button as profile button")
                        break
                except:
                    pass

        if profile_btn:
            profile_btn.click()
            page.wait_for_timeout(2000)
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v4_05_personal_center.png"
            )

            # Check for OpenRouter section
            page_html = page.content().lower()
            has_openrouter = "openrouter" in page_html
            has_api_key = "api" in page_html and "key" in page_html
            has_model = "模型" in page_html or "model" in page_html

            print(f"  OpenRouter mentioned: {has_openrouter}")
            print(f"  API key related: {has_api_key}")
            print(f"  Model selection: {has_model}")

            # Try to scroll down in the panel to find OpenRouter settings
            panel = page.locator(
                '[class*="panel"], [class*="drawer"], [class*="modal"]'
            ).last
            if panel:
                # Scroll within the panel
                panel.evaluate("el => el.scrollTop = el.scrollHeight")
                page.wait_for_timeout(500)
                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v4_06_personal_center_scrolled.png"
                )

                # Check for OpenRouter config section
                openrouter_section = page.locator("text=/OpenRouter/i").all()
                print(f"  OpenRouter text elements: {len(openrouter_section)}")

                config_section = page.locator("text=/自定义配置|custom.*config/i").all()
                print(f"  Config section elements: {len(config_section)}")

                # Look for mode toggle (平台托管 vs 我的 OpenRouter)
                mode_toggle = page.locator("text=/平台托管|我的.*OpenRouter/i").all()
                print(f"  Mode toggle elements: {len(mode_toggle)}")

                if has_openrouter or openrouter_section:
                    result5 = "PASS: OpenRouter settings found"
                else:
                    result5 = "FAIL: OpenRouter settings not found in personal center"
            else:
                result5 = "FAIL: Could not locate panel"
        else:
            result5 = "FAIL: Could not find personal center button"
            print("  FAIL: Could not find personal center button")

        # Final screenshot
        page.screenshot(
            path="D:/个人项目/pp/infinite-canvas/scripts/screenshots/v4_07_final.png"
        )

        browser.close()

    # Summary
    print("\n" + "=" * 60)
    print("QA VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"  1. Blank initial canvas: {result1}")
    print(f"  2. Image node affordances: {result3}")
    print(f"  3. Text node scrollbar: {result4}")
    print(f"  4. OpenRouter settings: {result5}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

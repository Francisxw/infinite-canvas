"""
QA verification script using the current local frontend port and artifact layout.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "qa_verify"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://localhost:15191"


def artifact_path(filename: str) -> str:
    return str(ARTIFACT_DIR / filename)


def main():
    result1 = "NOT_RUN"
    result2 = "NOT_RUN"
    result3 = "NOT_RUN"
    result4 = "NOT_RUN"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("=" * 60)
        print("QA VERIFICATION v5 - Final Report")
        print("=" * 60)

        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 1. BLANK CANVAS
        print("\n[1] BLANK INITIAL CANVAS")
        rf_nodes = page.locator(".react-flow__node").all()
        print(f"  React Flow nodes on load: {len(rf_nodes)}")
        page.screenshot(path=artifact_path("v5_01_blank_canvas.png"))
        result1 = "PASS" if len(rf_nodes) == 0 else f"FAIL: {len(rf_nodes)} nodes found"
        print(f"  Result: {result1}")

        # 2. CREATE IMAGE NODE VIA DOCK
        print("\n[2] IMAGE NODE AFFORDANCES")
        # Click the + button (新建节点)
        plus_btn = page.locator('[aria-label="新建节点"]').first
        if not plus_btn:
            plus_btn = (
                page.locator("button").filter(has=page.locator("svg.lucide-plus")).first
            )

        if plus_btn:
            print("  Clicking + button...")
            plus_btn.click()
            page.wait_for_timeout(1000)

            # Check for creation panel
            create_panel = page.locator('[data-testid="dock-create-panel"]')
            if create_panel.count() > 0:
                print("  Creation panel appeared!")
                page.screenshot(path=artifact_path("v5_02_creation_panel.png"))

                # Click image button
                img_btn = page.locator('[data-testid="dock-create-image"]')
                if img_btn.count() > 0:
                    print("  Clicking image creation button...")
                    img_btn.click()
                    page.wait_for_timeout(2000)
                    page.screenshot(path=artifact_path("v5_03_image_node_created.png"))

                    # Check for image node
                    nodes = page.locator(".react-flow__node").all()
                    print(f"  Nodes after creation: {len(nodes)}")

                    # Check for left/right port handles
                    left_handles = page.locator(
                        '[data-testid="image-node-input-port"]'
                    ).all()
                    right_handles = page.locator(
                        '[data-testid="image-node-output-port"]'
                    ).all()
                    print(f"  Left handles (input ports): {len(left_handles)}")
                    print(f"  Right handles (output ports): {len(right_handles)}")

                    # Check for the + buttons inside handles
                    handle_buttons = page.locator(
                        '[aria-label="image-node-input-port"], [aria-label="image-node-output-port"]'
                    ).all()
                    print(f"  Handle elements: {len(handle_buttons)}")

                    # Select the node to make handles more visible
                    if nodes:
                        nodes[0].click()
                        page.wait_for_timeout(500)
                        page.screenshot(
                            path=artifact_path("v5_04_image_node_selected.png")
                        )

                    result2 = (
                        "PASS"
                        if (len(left_handles) > 0 and len(right_handles) > 0)
                        else f"CHECK: left={len(left_handles)}, right={len(right_handles)}"
                    )
                else:
                    result2 = "FAIL: Image button not found"
            else:
                result2 = "FAIL: Creation panel not shown"
        else:
            result2 = "FAIL: Plus button not found"

        print(f"  Result: {result2}")

        # 3. TEXT NODE SCROLLBAR CHECK
        print("\n[3] TEXT NODE SCROLLBAR")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        plus_btn = page.locator('[aria-label="新建节点"]').first
        if plus_btn:
            plus_btn.click()
            page.wait_for_timeout(1000)

            txt_btn = page.locator('[data-testid="dock-create-text"]')
            if txt_btn.count() > 0:
                print("  Clicking text creation button...")
                txt_btn.click()
                page.wait_for_timeout(2000)
                page.screenshot(path=artifact_path("v5_05_text_node_created.png"))

                # Check text node for scrollbar
                textareas = page.locator("textarea").all()
                print(f"  Textarea elements: {len(textareas)}")

                for i, ta in enumerate(textareas[:3]):
                    try:
                        overflow_y = ta.evaluate("el => getComputedStyle(el).overflowY")
                        scroll_h = ta.evaluate("el => el.scrollHeight")
                        client_h = ta.evaluate("el => el.clientHeight")
                        has_scroll = scroll_h > client_h
                        print(
                            f"    Textarea {i}: overflowY={overflow_y}, scrollH={scroll_h}, clientH={client_h}, hasScroll={has_scroll}"
                        )

                        if i == 0:  # First textarea is the main one
                            if not has_scroll:
                                result3 = (
                                    "PASS: No unnecessary scrollbar on initial display"
                                )
                            else:
                                result3 = f"CHECK: Scrollbar present (scrollH={scroll_h}, clientH={client_h})"
                    except Exception as e:
                        print(f"    Error: {e}")

                # Also check the node's contenteditable areas
                editables = page.locator('[contenteditable="true"]').all()
                print(f"  Contenteditable elements: {len(editables)}")
            else:
                result3 = "FAIL: Text button not found"
        else:
            result3 = "FAIL: Plus button not found"

        print(f"  Result: {result3}")

        # 4. OPENROUTER SETTINGS IN PERSONAL CENTER
        print("\n[4] OPENROUTER SETTINGS")
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        profile_btn = page.locator('[aria-label="个人中心"]').first
        if profile_btn.count() > 0:
            print("  Clicking personal center button...")
            profile_btn.click()
            page.wait_for_timeout(2000)
            page.screenshot(path=artifact_path("v5_06_personal_center.png"))

            # Check for OpenRouter section
            page_html = page.content()
            has_openrouter = (
                "openrouter" in page_html.lower() or "OpenRouter" in page_html
            )
            has_custom_config = "自定义配置" in page_html
            has_api_key = "api" in page_html.lower() and "key" in page_html.lower()

            print(f"  OpenRouter mentioned: {has_openrouter}")
            print(f"  Custom config section: {has_custom_config}")
            print(f"  API key related: {has_api_key}")

            # Try scrolling the panel
            panel = page.locator('[class*="panel"]').last
            if panel:
                panel.evaluate("el => el.scrollTop = el.scrollHeight")
                page.wait_for_timeout(500)
                page.screenshot(
                    path=artifact_path("v5_07_personal_center_scrolled.png")
                )

            if has_openrouter or has_custom_config:
                result4 = "PASS: OpenRouter settings section found"
            else:
                result4 = "FAIL: OpenRouter settings not found"
        else:
            result4 = "FAIL: Personal center button not found"

        print(f"  Result: {result4}")

        # Final screenshot
        page.screenshot(path=artifact_path("v5_08_final.png"))

        browser.close()

    # Summary
    print("\n" + "=" * 60)
    print("QA VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"  1. Blank initial canvas: {result1}")
    print(f"  2. Image node affordances: {result2}")
    print(f"  3. Text node scrollbar: {result3}")
    print(f"  4. OpenRouter settings: {result4}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

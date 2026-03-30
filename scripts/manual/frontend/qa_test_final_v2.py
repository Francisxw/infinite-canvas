"""
QA Test Script for Infinite Canvas - Final Version 2
Verifies: blank canvas, image node controls, text node scrollbar, personal center settings
"""

import time
import random
import string
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5191"


def random_username():
    """Generate a random username for testing"""
    return f"testuser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"


def run_qa_tests():
    results = {
        "blank_canvas": {"status": "PENDING", "details": ""},
        "image_node_controls": {"status": "PENDING", "details": ""},
        "text_node_scrollbar": {"status": "PENDING", "details": ""},
        "personal_center_settings": {"status": "PENDING", "details": ""},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        try:
            print(f"[INFO] Navigating to {BASE_URL}")
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

            # ========================================
            # TEST (a): Initial state is blank canvas
            # ========================================
            print("\n[TEST (a)] Checking initial blank canvas state...")

            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_blank_canvas.png",
                full_page=True,
            )

            canvas_container = page.locator(".react-flow")
            if canvas_container.count() > 0:
                nodes = page.locator(".react-flow__node")
                node_count = nodes.count()

                minimap = page.locator(".react-flow__minimap")

                if node_count == 0:
                    results["blank_canvas"]["status"] = "PASS"
                    results["blank_canvas"]["details"] = (
                        f"Canvas loaded with 0 nodes. Minimap present: {minimap.count() > 0}"
                    )
                    print(f"  [PASS] Canvas is blank with {node_count} nodes")
                else:
                    results["blank_canvas"]["status"] = "FAIL"
                    results["blank_canvas"]["details"] = (
                        f"Expected 0 nodes, found {node_count}"
                    )
                    print(f"  [FAIL] Found {node_count} nodes on initial load")
            else:
                results["blank_canvas"]["status"] = "FAIL"
                results["blank_canvas"]["details"] = (
                    "React Flow canvas container not found"
                )
                print("  [FAIL] Canvas container not found")

            # ========================================
            # TEST (b): Image node left/right + controls visible
            # ========================================
            print("\n[TEST (b)] Checking image node controls visibility...")

            # Click the "new node" button (aria-label='新建节点')
            new_node_btn = page.locator('button[aria-label="新建节点"]')
            if new_node_btn.count() > 0:
                new_node_btn.first.click()
                time.sleep(1)

                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_new_node_menu.png",
                    full_page=True,
                )

                # Look for image option (图片 in Chinese)
                image_option = page.locator('button:has-text("图片")')
                if image_option.count() > 0:
                    print(f"  Found image option button")
                    image_option.first.click()
                    time.sleep(1)

            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_after_image_click.png",
                full_page=True,
            )

            # Check for image node
            image_node = page.locator(
                '.react-flow__node:has([data-preview-frame="image"])'
            )

            if image_node.count() > 0:
                print(f"  Found image node, clicking to select...")
                image_node.first.click()
                time.sleep(0.5)

                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_image_node_selected.png",
                    full_page=True,
                )

                # Check for side ports
                left_port = page.locator('[data-testid="image-node-input-port"]')
                right_port = page.locator('[data-testid="image-node-output-port"]')

                # Check visibility
                left_visible = left_port.count() > 0 and left_port.first.is_visible()
                right_visible = right_port.count() > 0 and right_port.first.is_visible()

                # Check if the node has overflow-visible (not clipped)
                node_style = image_node.first.evaluate("""
                    el => {
                        const style = window.getComputedStyle(el);
                        return {
                            overflow: style.overflow,
                            overflowX: style.overflowX,
                            overflowY: style.overflowY
                        }
                    }
                """)

                overflow_ok = (
                    node_style.get("overflow") == "visible"
                    or node_style.get("overflowX") == "visible"
                )

                if left_visible and right_visible and overflow_ok:
                    results["image_node_controls"]["status"] = "PASS"
                    results["image_node_controls"]["details"] = (
                        f"Left port: {left_visible}, Right port: {right_visible}, Overflow: {node_style}"
                    )
                    print(f"  [PASS] Image node ports visible and not clipped")
                else:
                    results["image_node_controls"]["status"] = "FAIL"
                    results["image_node_controls"]["details"] = (
                        f"Left: {left_visible}, Right: {right_visible}, Overflow: {node_style}"
                    )
                    print(
                        f"  [FAIL] Ports or overflow issue - Left: {left_visible}, Right: {right_visible}"
                    )
            else:
                results["image_node_controls"]["status"] = "FAIL"
                results["image_node_controls"]["details"] = "Image node not found"
                print("  [FAIL] Image node not found")

            # ========================================
            # TEST (c): Text node initial display has no unnecessary scrollbar
            # ========================================
            print("\n[TEST (c)] Checking text node scrollbar...")

            # First, click on empty canvas area to deselect any node
            canvas = page.locator(".react-flow__pane")
            if canvas.count() > 0:
                canvas.first.click(position={"x": 100, "y": 100})
                time.sleep(0.5)

            # Click new node button again
            new_node_btn = page.locator('button[aria-label="新建节点"]')
            if new_node_btn.count() > 0:
                new_node_btn.first.click()
                time.sleep(1)

                # Look for text option (文本 in Chinese)
                text_option = page.locator('button:has-text("文本")')
                if text_option.count() > 0:
                    print(f"  Found text option button")
                    text_option.first.click()
                    time.sleep(1)

            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_text_node.png",
                full_page=True,
            )

            # Check for text node
            text_node = page.locator(
                '.react-flow__node:has([data-preview-frame="text"])'
            )

            if text_node.count() > 0:
                print(f"  Found text node, clicking to select...")
                # Use force=True to click even if another element intercepts
                text_node.first.click(force=True)
                time.sleep(0.5)

                text_preview = page.locator(
                    '[data-testid="text-preview-frame"], [data-preview-frame="text"]'
                )

                if text_preview.count() > 0:
                    # Check overflow styles
                    overflow_info = text_preview.first.evaluate("""
                        el => {
                            const style = window.getComputedStyle(el);
                            return {
                                overflowY: style.overflowY,
                                overflowX: style.overflowX,
                                overflow: style.overflow
                            }
                        }
                    """)

                    # Check the display element
                    text_display = page.locator('[data-testid="text-node-display"]')
                    has_scrollbar = False
                    display_overflow = "unknown"

                    if text_display.count() > 0:
                        display_info = text_display.first.evaluate("""
                            el => {
                                const style = window.getComputedStyle(el);
                                return {
                                    overflowY: style.overflowY,
                                    overflowX: style.overflowX,
                                    scrollHeight: el.scrollHeight,
                                    clientHeight: el.clientHeight
                                }
                            }
                        """)
                        display_overflow = display_info.get("overflowY", "unknown")
                        has_scrollbar = display_info.get(
                            "scrollHeight", 0
                        ) > display_info.get("clientHeight", 0)

                    page.screenshot(
                        path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_text_node_selected.png",
                        full_page=True,
                    )

                    # Check if overflow is hidden (no scrollbar)
                    frame_overflow = overflow_info.get("overflowY", "")
                    if (
                        frame_overflow == "hidden"
                        or display_overflow == "hidden"
                        or not has_scrollbar
                    ):
                        results["text_node_scrollbar"]["status"] = "PASS"
                        results["text_node_scrollbar"]["details"] = (
                            f"Frame overflow: {overflow_info}, Display overflow: {display_overflow}, Has scrollbar: {has_scrollbar}"
                        )
                        print(f"  [PASS] No unnecessary scrollbar")
                    else:
                        results["text_node_scrollbar"]["status"] = "FAIL"
                        results["text_node_scrollbar"]["details"] = (
                            f"Scrollbar detected. Frame: {overflow_info}, Display: {display_overflow}"
                        )
                        print(f"  [FAIL] Scrollbar present")
                else:
                    results["text_node_scrollbar"]["status"] = "FAIL"
                    results["text_node_scrollbar"]["details"] = (
                        "Text preview frame not found"
                    )
                    print("  [FAIL] Text preview frame not found")
            else:
                results["text_node_scrollbar"]["status"] = "FAIL"
                results["text_node_scrollbar"]["details"] = "Text node not found"
                print("  [FAIL] Text node not found")

            # ========================================
            # TEST (d): Personal center with OpenRouter settings
            # ========================================
            print("\n[TEST (d)] Checking personal center settings...")

            # Click on the last button (user/settings icon) to open Personal Center
            buttons = page.locator("button")
            if buttons.count() >= 7:
                print(f"  Clicking user/settings button (button 6)...")
                buttons.nth(6).click()
                time.sleep(1)

                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_personal_center_modal.png",
                    full_page=True,
                )

                # Find email input (placeholder='name@example.com')
                email_input = page.locator('input[placeholder="name@example.com"]')
                # Find password input (type='password')
                password_input = page.locator('input[type="password"]')

                if email_input.count() > 0 and password_input.count() > 0:
                    print(f"  Found email and password inputs")

                    # Look for register tab (注册)
                    register_tab = page.locator(
                        'button:has-text("注册"), a:has-text("注册")'
                    )
                    if register_tab.count() > 0:
                        print(f"  Found register tab, clicking...")
                        register_tab.first.click()
                        time.sleep(0.5)

                    # Fill registration form
                    username = random_username()
                    password = "TestPass123!"

                    email_input.first.fill(f"{username}@example.com")
                    password_input.first.fill(password)

                    page.screenshot(
                        path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_filled_register_form.png",
                        full_page=True,
                    )

                    # Submit registration
                    submit_btn = page.locator('button[type="submit"]')
                    if submit_btn.count() > 0:
                        print(f"  Found submit button, clicking...")
                        submit_btn.first.click()
                        time.sleep(2)

                        page.screenshot(
                            path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_after_register.png",
                            full_page=True,
                        )

                        # After registration, check for model selectors
                        # The personal center should now show settings

                        # Look for model selectors
                        all_selects = page.locator("select")
                        select_count = all_selects.count()

                        # Look for model-related labels
                        text_model = page.locator(
                            'text=文本模型, text=Text Model, label:has-text("文本")'
                        )
                        image_model = page.locator(
                            'text=图像模型, text=Image Model, label:has-text("图像")'
                        )
                        video_model = page.locator(
                            'text=视频模型, text=Video Model, label:has-text("视频")'
                        )

                        has_text = text_model.count() > 0
                        has_image = image_model.count() > 0
                        has_video = video_model.count() > 0

                        if has_text and has_image and has_video:
                            results["personal_center_settings"]["status"] = "PASS"
                            results["personal_center_settings"]["details"] = (
                                f"Found all 3 model selectors. Selects: {select_count}"
                            )
                            print(f"  [PASS] Personal center has all 3 model selectors")
                        else:
                            results["personal_center_settings"]["status"] = "FAIL"
                            results["personal_center_settings"]["details"] = (
                                f"Missing selectors - Text: {has_text}, Image: {has_image}, Video: {has_video}. Total selects: {select_count}"
                            )
                            print(f"  [FAIL] Not all model selectors found")
                    else:
                        results["personal_center_settings"]["status"] = "FAIL"
                        results["personal_center_settings"]["details"] = (
                            "Submit button not found"
                        )
                        print("  [FAIL] Submit button not found")
                else:
                    results["personal_center_settings"]["status"] = "FAIL"
                    results["personal_center_settings"]["details"] = (
                        f"Email input: {email_input.count()}, Password input: {password_input.count()}"
                    )
                    print(f"  [FAIL] Email/password inputs not found")
            else:
                results["personal_center_settings"]["status"] = "FAIL"
                results["personal_center_settings"]["details"] = (
                    "User/settings button not found"
                )
                print("  [FAIL] User/settings button not found")

        except Exception as e:
            print(f"\n[ERROR] Test execution failed: {str(e)}")
            import traceback

            traceback.print_exc()
            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_error.png",
                full_page=True,
            )
            for key in results:
                if results[key]["status"] == "PENDING":
                    results[key]["status"] = "ERROR"
                    results[key]["details"] = str(e)
        finally:
            browser.close()

    return results


def print_report(results):
    print("\n" + "=" * 60)
    print("QA TEST REPORT - Infinite Canvas")
    print("=" * 60)

    test_names = {
        "blank_canvas": "(a) Initial blank canvas state",
        "image_node_controls": "(b) Image node left/right + controls visibility",
        "text_node_scrollbar": "(c) Text node no unnecessary scrollbar",
        "personal_center_settings": "(d) Personal center OpenRouter settings with 3 selectors",
    }

    pass_count = sum(1 for r in results.values() if r["status"] == "PASS")
    total_count = len(results)

    for key, name in test_names.items():
        status = results[key]["status"]
        details = results[key]["details"]

        status_symbol = (
            "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[ERR]"
        )
        print(f"\n{status_symbol} {name}")
        print(f"  Status: {status}")
        if details:
            print(f"  Details: {details}")

    print("\n" + "-" * 60)
    print(f"SUMMARY: {pass_count}/{total_count} tests passed")

    if pass_count == total_count:
        print("RESULT: ALL TESTS PASSED")
    else:
        print("RESULT: SOME TESTS FAILED")

    print("=" * 60)

    return pass_count == total_count


if __name__ == "__main__":
    print("Starting QA Tests for Infinite Canvas...")
    results = run_qa_tests()
    all_passed = print_report(results)
    exit(0 if all_passed else 1)

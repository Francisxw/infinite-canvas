"""
QA Test Script for Infinite Canvas - Version 2
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
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_load_state("networkidle")
            time.sleep(3)

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

                # Take screenshot to see the menu
                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_new_node_menu.png",
                    full_page=True,
                )

                # Look for image node option in the menu
                # Try various selectors
                image_option = page.locator(
                    'text=Image, text=image, [data-node-type="image-node"], button:has-text("Image")'
                )
                if image_option.count() > 0:
                    image_option.first.click()
                    time.sleep(1)
                else:
                    # Try clicking on any menu item that might be image
                    menu_items = page.locator(
                        '[role="menuitem"], [class*="menu"] button, [class*="dropdown"] button'
                    )
                    print(f"  Found {menu_items.count()} menu items")
                    for i in range(menu_items.count()):
                        item = menu_items.nth(i)
                        text = item.text_content() or ""
                        print(f"    Menu item {i}: '{text[:30]}'")

            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_after_new_node.png",
                full_page=True,
            )

            # Check for image node
            image_node = page.locator(
                '.react-flow__node:has([data-preview-frame="image"])'
            )

            if image_node.count() > 0:
                image_node.first.click()
                time.sleep(0.5)

                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_image_node_selected.png",
                    full_page=True,
                )

                # Check for side ports
                left_port = page.locator('[data-testid="image-node-input-port"]')
                right_port = page.locator('[data-testid="image-node-output-port"]')

                # Also check for handle elements
                left_handle = page.locator(
                    '.react-flow__handle-left, [class*="handle"][class*="left"]'
                )
                right_handle = page.locator(
                    '.react-flow__handle-right, [class*="handle"][class*="right"]'
                )

                left_visible = (
                    left_port.count() > 0 and left_port.first.is_visible()
                ) or (left_handle.count() > 0 and left_handle.first.is_visible())
                right_visible = (
                    right_port.count() > 0 and right_port.first.is_visible()
                ) or (right_handle.count() > 0 and right_handle.first.is_visible())

                if left_visible and right_visible:
                    results["image_node_controls"]["status"] = "PASS"
                    results["image_node_controls"]["details"] = (
                        f"Left port visible: {left_visible}, Right port visible: {right_visible}"
                    )
                    print(f"  [PASS] Image node ports are visible")
                else:
                    results["image_node_controls"]["status"] = "FAIL"
                    results["image_node_controls"]["details"] = (
                        f"Left port visible: {left_visible}, Right port visible: {right_visible}"
                    )
                    print(
                        f"  [FAIL] Ports not visible - Left: {left_visible}, Right: {right_visible}"
                    )
            else:
                # Check if any node was created
                any_node = page.locator(".react-flow__node")
                if any_node.count() > 0:
                    node_html = any_node.first.inner_html()[:200]
                    print(f"  Found node but not image type. HTML: {node_html}")
                results["image_node_controls"]["status"] = "FAIL"
                results["image_node_controls"]["details"] = "Image node not found"
                print("  [FAIL] Image node not found")

            # ========================================
            # TEST (c): Text node initial display has no unnecessary scrollbar
            # ========================================
            print("\n[TEST (c)] Checking text node scrollbar...")

            # Click new node button again
            new_node_btn = page.locator('button[aria-label="新建节点"]')
            if new_node_btn.count() > 0:
                new_node_btn.first.click()
                time.sleep(1)

                # Look for text node option
                text_option = page.locator(
                    'text=Text, text=text, [data-node-type="text-node"], button:has-text("Text")'
                )
                if text_option.count() > 0:
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
                text_node.first.click()
                time.sleep(0.5)

                text_preview = page.locator(
                    '[data-testid="text-preview-frame"], [data-preview-frame="text"]'
                )

                if text_preview.count() > 0:
                    overflow_style = text_preview.first.evaluate("""
                        el => window.getComputedStyle(el).overflowY
                    """)

                    text_display = page.locator('[data-testid="text-node-display"]')
                    has_scrollbar = False

                    if text_display.count() > 0:
                        display_info = text_display.first.evaluate("""
                            el => {
                                const style = window.getComputedStyle(el);
                                return {
                                    overflowY: style.overflowY,
                                    scrollHeight: el.scrollHeight,
                                    clientHeight: el.clientHeight
                                }
                            }
                        """)
                        has_scrollbar = display_info.get(
                            "scrollHeight", 0
                        ) > display_info.get("clientHeight", 0)

                    page.screenshot(
                        path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_text_node_selected.png",
                        full_page=True,
                    )

                    if overflow_style == "hidden" or not has_scrollbar:
                        results["text_node_scrollbar"]["status"] = "PASS"
                        results["text_node_scrollbar"]["details"] = (
                            f"Frame overflow: {overflow_style}, Has scrollbar: {has_scrollbar}"
                        )
                        print(f"  [PASS] No unnecessary scrollbar")
                    else:
                        results["text_node_scrollbar"]["status"] = "FAIL"
                        results["text_node_scrollbar"]["details"] = (
                            f"Scrollbar detected. Overflow: {overflow_style}"
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

            # Look for settings/account button (aria-label='设置' or similar)
            settings_btn = page.locator(
                'button[aria-label="设置"], button[aria-label="账户设置"], button:has-text("设置")'
            )

            if settings_btn.count() > 0:
                settings_btn.first.click()
                time.sleep(1)

                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_settings_menu.png",
                    full_page=True,
                )

                # Look for login/register option
                login_option = page.locator(
                    'text=登录, text=Login, text=注册, text=Register, button:has-text("登录")'
                )
                if login_option.count() > 0:
                    login_option.first.click()
                    time.sleep(1)

            # Alternative: look for direct login button
            login_btn = page.locator(
                'button:has-text("登录"), button:has-text("Login"), [data-testid="login-button"]'
            )
            if (
                login_btn.count() > 0
                and results["personal_center_settings"]["status"] == "PENDING"
            ):
                login_btn.first.click()
                time.sleep(1)

            page.screenshot(
                path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_login_modal.png",
                full_page=True,
            )

            # Check if we're on a login page/modal
            username_input = page.locator(
                'input[name="username"], input[type="text"], input[placeholder*="用户"]'
            )
            password_input = page.locator(
                'input[name="password"], input[type="password"], input[placeholder*="密码"]'
            )

            if username_input.count() > 0 and password_input.count() > 0:
                # Look for register tab
                register_tab = page.locator(
                    'text=注册, text=Register, a:has-text("注册"), button:has-text("注册")'
                )
                if register_tab.count() > 0:
                    register_tab.first.click()
                    time.sleep(0.5)

                # Fill registration form
                username = random_username()
                password = "TestPass123!"

                username_input.first.fill(username)
                password_input.first.fill(password)

                # Check for confirm password
                confirm_input = page.locator(
                    'input[name="confirmPassword"], input[placeholder*="确认"]'
                )
                if confirm_input.count() > 0:
                    confirm_input.first.fill(password)

                page.screenshot(
                    path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_filled_form.png",
                    full_page=True,
                )

                # Submit
                submit_btn = page.locator(
                    'button[type="submit"], button:has-text("注册"), button:has-text("Register"), button:has-text("创建")'
                )
                if submit_btn.count() > 0:
                    submit_btn.first.click()
                    time.sleep(2)

                    page.screenshot(
                        path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_after_register.png",
                        full_page=True,
                    )

                    # Check for user menu
                    user_menu = page.locator(
                        '[data-testid="user-menu"], button[aria-label="用户菜单"], .user-avatar'
                    )
                    if user_menu.count() > 0:
                        user_menu.first.click()
                        time.sleep(1)

                        # Look for profile/settings
                        profile_link = page.locator(
                            "text=个人中心, text=Profile, text=设置, text=Settings"
                        )
                        if profile_link.count() > 0:
                            profile_link.first.click()
                            time.sleep(1)

                        page.screenshot(
                            path="D:/个人项目/pp/infinite-canvas/frontend/tmp/qa_personal_center.png",
                            full_page=True,
                        )

                        # Check for model selectors
                        # Look for select elements or dropdowns
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
                            "User menu not found"
                        )
                        print("  [FAIL] User menu not found")
                else:
                    results["personal_center_settings"]["status"] = "FAIL"
                    results["personal_center_settings"]["details"] = (
                        "Submit button not found"
                    )
                    print("  [FAIL] Submit button not found")
            else:
                results["personal_center_settings"]["status"] = "FAIL"
                results["personal_center_settings"]["details"] = "Login form not found"
                print("  [FAIL] Login form not found")

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

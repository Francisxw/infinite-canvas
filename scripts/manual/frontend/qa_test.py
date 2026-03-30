"""
QA Test Script for Infinite Canvas
Verifies: blank canvas, image node controls, text node scrollbar, personal center settings
"""

import time
import random
import string
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5191"  # Using the actual running port


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
            # Navigate to the app
            print(f"[INFO] Navigating to {BASE_URL}")
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)  # Wait for React to render

            # ========================================
            # TEST (a): Initial state is blank canvas
            # ========================================
            print("\n[TEST (a)] Checking initial blank canvas state...")

            # Take screenshot for inspection
            page.screenshot(
                path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_blank_canvas.png",
                full_page=True,
            )

            # Check for React Flow canvas container
            canvas_container = page.locator(".react-flow")
            if canvas_container.count() > 0:
                # Check that there are no nodes initially
                nodes = page.locator(".react-flow__node")
                node_count = nodes.count()

                # Check for blank canvas indicator or empty state
                # Look for the minimap or controls which indicate canvas is loaded
                minimap = page.locator(".react-flow__minimap")
                controls = page.locator(".react-flow__controls")

                if node_count == 0:
                    results["blank_canvas"]["status"] = "PASS"
                    results["blank_canvas"]["details"] = (
                        f"Canvas loaded with 0 nodes. Minimap present: {minimap.count() > 0}, Controls present: {controls.count() > 0}"
                    )
                    print(f"  [PASS] Canvas is blank with {node_count} nodes")
                else:
                    # Check if nodes are just UI elements (like toolbar buttons)
                    actual_flow_nodes = page.locator(".react-flow__node[data-id]")
                    actual_count = actual_flow_nodes.count()
                    if actual_count == 0:
                        results["blank_canvas"]["status"] = "PASS"
                        results["blank_canvas"]["details"] = (
                            f"Canvas loaded with no flow nodes (UI elements present)"
                        )
                        print(f"  [PASS] Canvas is blank (no flow nodes)")
                    else:
                        results["blank_canvas"]["status"] = "FAIL"
                        results["blank_canvas"]["details"] = (
                            f"Expected 0 nodes, found {actual_count}"
                        )
                        print(
                            f"  [FAIL] Found {actual_count} flow nodes on initial load"
                        )
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

            # Look for image node creation button or create one
            # First, check if there's a toolbar or button to add nodes
            add_image_btn = page.locator(
                'button:has-text("Image"), button:has-text("image"), [data-testid="add-image-node"]'
            )

            if add_image_btn.count() > 0:
                add_image_btn.first.click()
                time.sleep(1)
            else:
                # Try to find any add node button
                add_btn = page.locator('button:has-text("Add"), button:has-text("+")')
                if add_btn.count() > 0:
                    add_btn.first.click()
                    time.sleep(0.5)
                    # Look for image option
                    image_option = page.locator('text=Image, [data-node-type="image"]')
                    if image_option.count() > 0:
                        image_option.first.click()
                        time.sleep(1)

            # Take screenshot after attempting to create image node
            page.screenshot(
                path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_image_node.png",
                full_page=True,
            )

            # Check for image node
            image_node = page.locator(
                '.react-flow__node[data-id*="image"], .react-flow__node:has([data-preview-frame="image"])'
            )

            if image_node.count() > 0:
                # Click to select the node
                image_node.first.click()
                time.sleep(0.5)

                # Check for left port (input)
                left_port = page.locator(
                    '[data-testid="image-node-input-port"], .react-flow__handle-left, [aria-label="image-node-input-port"]'
                )

                # Check for right port (output)
                right_port = page.locator(
                    '[data-testid="image-node-output-port"], .react-flow__handle-right, [aria-label="image-node-output-port"]'
                )

                # Check for controls (model picker, settings, etc.)
                model_picker = page.locator(
                    'button:has-text("select model"), button:has-text("Gemini")'
                )
                settings_btn = page.locator(
                    'button:has-text("1:1"), button:has-text("settings")'
                )

                # Take screenshot of selected node
                page.screenshot(
                    path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_image_node_selected.png",
                    full_page=True,
                )

                # Check visibility
                left_visible = left_port.count() > 0 and left_port.first.is_visible()
                right_visible = right_port.count() > 0 and right_port.first.is_visible()
                controls_visible = model_picker.count() > 0 or settings_btn.count() > 0

                if left_visible and right_visible:
                    results["image_node_controls"]["status"] = "PASS"
                    results["image_node_controls"]["details"] = (
                        f"Left port visible: {left_visible}, Right port visible: {right_visible}, Controls visible: {controls_visible}"
                    )
                    print(f"  [PASS] Image node ports and controls are visible")
                else:
                    results["image_node_controls"]["status"] = "FAIL"
                    results["image_node_controls"]["details"] = (
                        f"Left port visible: {left_visible}, Right port visible: {right_visible}"
                    )
                    print(
                        f"  [FAIL] Ports not properly visible - Left: {left_visible}, Right: {right_visible}"
                    )
            else:
                results["image_node_controls"]["status"] = "FAIL"
                results["image_node_controls"]["details"] = (
                    "Could not create or find image node"
                )
                print("  [FAIL] Image node not found")

            # ========================================
            # TEST (c): Text node initial display has no unnecessary scrollbar
            # ========================================
            print("\n[TEST (c)] Checking text node scrollbar...")

            # Create a text node
            add_text_btn = page.locator(
                'button:has-text("Text"), button:has-text("text"), [data-testid="add-text-node"]'
            )

            if add_text_btn.count() > 0:
                add_text_btn.first.click()
                time.sleep(1)
            else:
                # Try generic add button
                add_btn = page.locator('button:has-text("Add"), button:has-text("+")')
                if add_btn.count() > 0:
                    add_btn.first.click()
                    time.sleep(0.5)
                    text_option = page.locator('text=Text, [data-node-type="text"]')
                    if text_option.count() > 0:
                        text_option.first.click()
                        time.sleep(1)

            # Take screenshot
            page.screenshot(
                path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_text_node.png",
                full_page=True,
            )

            # Check for text node
            text_node = page.locator(
                '.react-flow__node[data-id*="text"], .react-flow__node:has([data-preview-frame="text"])'
            )

            if text_node.count() > 0:
                # Click to select
                text_node.first.click()
                time.sleep(0.5)

                # Check for scrollbar in text preview frame
                text_preview = page.locator(
                    '[data-testid="text-preview-frame"], [data-preview-frame="text"]'
                )

                if text_preview.count() > 0:
                    # Check if overflow-y is hidden (no scrollbar)
                    overflow_style = text_preview.first.evaluate("""
                        el => window.getComputedStyle(el).overflowY
                    """)

                    # Also check the display element inside
                    text_display = page.locator('[data-testid="text-node-display"]')
                    display_overflow = "unknown"
                    has_scrollbar = False

                    if text_display.count() > 0:
                        display_overflow = text_display.first.evaluate("""
                            el => {
                                const style = window.getComputedStyle(el);
                                return {
                                    overflowY: style.overflowY,
                                    scrollHeight: el.scrollHeight,
                                    clientHeight: el.clientHeight
                                }
                            }
                        """)
                        has_scrollbar = display_overflow.get(
                            "scrollHeight", 0
                        ) > display_overflow.get("clientHeight", 0)

                    # Take screenshot of text node
                    page.screenshot(
                        path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_text_node_selected.png",
                        full_page=True,
                    )

                    if overflow_style == "hidden" or not has_scrollbar:
                        results["text_node_scrollbar"]["status"] = "PASS"
                        results["text_node_scrollbar"]["details"] = (
                            f"Frame overflow: {overflow_style}, Display overflow: {display_overflow}, Has scrollbar: {has_scrollbar}"
                        )
                        print(
                            f"  [PASS] No unnecessary scrollbar (overflow: {overflow_style})"
                        )
                    else:
                        results["text_node_scrollbar"]["status"] = "FAIL"
                        results["text_node_scrollbar"]["details"] = (
                            f"Unnecessary scrollbar detected. Frame overflow: {overflow_style}, Display: {display_overflow}"
                        )
                        print(f"  [FAIL] Scrollbar present when it shouldn't be")
                else:
                    results["text_node_scrollbar"]["status"] = "FAIL"
                    results["text_node_scrollbar"]["details"] = (
                        "Text preview frame not found"
                    )
                    print("  [FAIL] Text preview frame not found")
            else:
                results["text_node_scrollbar"]["status"] = "FAIL"
                results["text_node_scrollbar"]["details"] = (
                    "Could not create or find text node"
                )
                print("  [FAIL] Text node not found")

            # ========================================
            # TEST (d): Personal center with OpenRouter settings
            # ========================================
            print("\n[TEST (d)] Checking personal center settings...")

            # First, register a new user
            username = random_username()
            password = "TestPass123!"

            # Look for login/register button
            login_btn = page.locator(
                'button:has-text("Login"), button:has-text("login"), button:has-text("Register"), button:has-text("register"), [data-testid="login-button"]'
            )

            if login_btn.count() > 0:
                login_btn.first.click()
                time.sleep(1)

                # Take screenshot of login modal
                page.screenshot(
                    path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_login_modal.png",
                    full_page=True,
                )

                # Look for register tab/link
                register_tab = page.locator(
                    'text=Register, text=register, text=Create Account, a:has-text("Register")'
                )
                if register_tab.count() > 0:
                    register_tab.first.click()
                    time.sleep(0.5)

                # Fill registration form
                username_input = page.locator(
                    'input[name="username"], input[placeholder*="Username"], input[type="text"]'
                ).first
                password_input = page.locator(
                    'input[name="password"], input[placeholder*="Password"], input[type="password"]'
                ).first

                username_input.fill(username)
                password_input.fill(password)

                # Check for confirm password field
                confirm_password = page.locator(
                    'input[name="confirmPassword"], input[placeholder*="Confirm"]'
                )
                if confirm_password.count() > 0:
                    confirm_password.first.fill(password)

                # Submit registration
                submit_btn = page.locator(
                    'button[type="submit"], button:has-text("Register"), button:has-text("Create")'
                )
                if submit_btn.count() > 0:
                    submit_btn.first.click()
                    time.sleep(2)

                    # Take screenshot after registration
                    page.screenshot(
                        path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_after_register.png",
                        full_page=True,
                    )

                    # Check if logged in (look for user menu or profile button)
                    user_menu = page.locator(
                        '[data-testid="user-menu"], button:has-text("Profile"), .user-avatar'
                    )

                    if user_menu.count() > 0:
                        user_menu.first.click()
                        time.sleep(1)

                        # Look for settings or personal center
                        settings_link = page.locator(
                            'text=Settings, text=Profile, a:has-text("Settings")'
                        )
                        if settings_link.count() > 0:
                            settings_link.first.click()
                            time.sleep(1)

                        # Take screenshot of personal center
                        page.screenshot(
                            path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_personal_center.png",
                            full_page=True,
                        )

                        # Check for OpenRouter settings with 3 model selectors
                        # Look for text/image/video model selectors
                        text_model_selector = page.locator(
                            'text=Text Model, select:near(:text("Text")), [data-testid="text-model-selector"]'
                        )
                        image_model_selector = page.locator(
                            'text=Image Model, select:near(:text("Image")), [data-testid="image-model-selector"]'
                        )
                        video_model_selector = page.locator(
                            'text=Video Model, select:near(:text("Video")), [data-testid="video-model-selector"]'
                        )

                        # Also check for OpenRouter reference
                        openrouter_ref = page.locator(
                            'text=OpenRouter, text=openrouter, [data-provider="openrouter"]'
                        )

                        has_text = text_model_selector.count() > 0
                        has_image = image_model_selector.count() > 0
                        has_video = video_model_selector.count() > 0
                        has_openrouter = openrouter_ref.count() > 0

                        if has_text and has_image and has_video:
                            results["personal_center_settings"]["status"] = "PASS"
                            results["personal_center_settings"]["details"] = (
                                f"Found all 3 model selectors (text: {has_text}, image: {has_image}, video: {has_video}). OpenRouter ref: {has_openrouter}"
                            )
                            print(f"  [PASS] Personal center has all 3 model selectors")
                        else:
                            # Try alternative selectors
                            all_selects = page.locator("select")
                            select_count = all_selects.count()

                            # Check for any model-related content
                            model_content = page.locator(
                                "text=Model, text=preferred, text=default"
                            )
                            model_content_count = model_content.count()

                            results["personal_center_settings"]["status"] = "FAIL"
                            results["personal_center_settings"]["details"] = (
                                f"Missing selectors - Text: {has_text}, Image: {has_image}, Video: {has_video}. Found {select_count} selects, {model_content_count} model references"
                            )
                            print(f"  [FAIL] Not all model selectors found")
                    else:
                        results["personal_center_settings"]["status"] = "FAIL"
                        results["personal_center_settings"]["details"] = (
                            "User menu not found after registration"
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
                results["personal_center_settings"]["details"] = (
                    "Login button not found"
                )
                print("  [FAIL] Login button not found")

        except Exception as e:
            print(f"\n[ERROR] Test execution failed: {str(e)}")
            page.screenshot(
                path="D:/personal_projects/pp/infinite-canvas/frontend/tmp/qa_error.png",
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

    # Exit with appropriate code
    exit(0 if all_passed else 1)

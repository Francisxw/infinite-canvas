from playwright.sync_api import sync_playwright
import time
import random
import string


def generate_random_user():
    """Generate random user credentials for testing"""
    username = "testuser_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=8)
    )
    password = "TestPass123!"
    return username, password


def test_blank_canvas(page):
    """Test (a): Verify initial state is a blank canvas"""
    print("\n=== Test (a): Blank Canvas ===")

    # Navigate to the app
    page.goto("http://127.0.0.1:5180")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Take screenshot of initial state
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_a_blank_canvas.png",
        full_page=True,
    )

    # Check for canvas element (React Flow uses div with class react-flow)
    react_flow = page.locator(".react-flow")
    react_flow_count = react_flow.count()
    print(f"React Flow elements found: {react_flow_count}")

    # Check if there are any nodes on the canvas
    nodes = page.locator(".react-flow__node")
    node_count = nodes.count()
    print(f"Node elements found: {node_count}")

    # Check if canvas area is empty (no nodes)
    is_blank = node_count == 0

    return {
        "test": "blank_canvas",
        "passed": is_blank,
        "details": f"React Flow elements: {react_flow_count}, Node elements: {node_count}",
        "screenshot": "test_a_blank_canvas.png",
    }


def test_image_node_controls(page):
    """Test (b): Verify image node left/right + controls are visible and not clipped"""
    print("\n=== Test (b): Image Node Controls ===")

    page.goto("http://127.0.0.1:5180")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Click on the "+" button in the bottom toolbar to open node creation menu
    # The "+" button is the first circular button in the bottom toolbar
    add_button = page.locator('button:has-text("+")')
    if add_button.count() > 0:
        add_button.first.click()
        time.sleep(1)

        # Take screenshot to see menu
        page.screenshot(
            path="D:\\个人项目\\pp\\infinite-canvas\\test_b_menu.png", full_page=True
        )

        # Look for image node option in the menu
        image_option = page.locator('text="图片"')
        if image_option.count() > 0:
            image_option.first.click()
            time.sleep(2)
        else:
            # Try English
            image_option = page.locator('text="Image"')
            if image_option.count() > 0:
                image_option.first.click()
                time.sleep(2)

    # Take screenshot after creating node
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_b_node_created.png",
        full_page=True,
    )

    # Look for image nodes
    image_nodes = page.locator(".react-flow__node")
    node_count = image_nodes.count()
    print(f"Total nodes found: {node_count}")

    if node_count > 0:
        # Click on the first node to select it
        image_nodes.first.click()
        time.sleep(1)

        # Take screenshot of selected node
        page.screenshot(
            path="D:\\个人项目\\pp\\infinite-canvas\\test_b_node_selected.png",
            full_page=True,
        )

        # Check for control points/handles (ports)
        handles = page.locator(".react-flow__handle")
        handle_count = handles.count()
        print(f"Handle elements found: {handle_count}")

        # Check if handles are visible
        visible_handles = 0
        for i in range(handle_count):
            handle = handles.nth(i)
            if handle.is_visible():
                visible_handles += 1

        print(f"Visible handles: {visible_handles}")

        # Check for left/right specific handles
        left_handles = page.locator(".react-flow__handle-left")
        right_handles = page.locator(".react-flow__handle-right")

        left_count = left_handles.count()
        right_count = right_handles.count()
        print(f"Left handles: {left_count}, Right handles: {right_count}")

        # Check if handles are clipped by checking their bounding boxes
        handles_clipped = False
        for i in range(handle_count):
            handle = handles.nth(i)
            if handle.is_visible():
                box = handle.bounding_box()
                if box:
                    # Check if handle is within viewport
                    if box["x"] < 0 or box["y"] < 0:
                        handles_clipped = True
                        print(f"Handle {i} is clipped: x={box['x']}, y={box['y']}")

        passed = visible_handles > 0 and not handles_clipped
    else:
        print("No nodes found to test")
        passed = False
        visible_handles = 0
        left_count = 0
        right_count = 0

    return {
        "test": "image_node_controls",
        "passed": passed,
        "details": f"Nodes: {node_count}, Visible handles: {visible_handles}, Left: {left_count}, Right: {right_count}, Clipped: {handles_clipped if node_count > 0 else 'N/A'}",
        "screenshot": "test_b_node_selected.png",
    }


def test_text_node_scrollbar(page):
    """Test (c): Verify text node initial display has no unnecessary scrollbar"""
    print("\n=== Test (c): Text Node Scrollbar ===")

    page.goto("http://127.0.0.1:5180")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Click on the "+" button to open node creation menu
    add_button = page.locator('button:has-text("+")')
    if add_button.count() > 0:
        add_button.first.click()
        time.sleep(1)

        # Look for text node option
        text_option = page.locator('text="文本"')
        if text_option.count() > 0:
            text_option.first.click()
            time.sleep(2)
        else:
            # Try English
            text_option = page.locator('text="Text"')
            if text_option.count() > 0:
                text_option.first.click()
                time.sleep(2)

    # Take screenshot
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_c_text_node.png", full_page=True
    )

    # Look for text nodes
    text_nodes = page.locator(".react-flow__node")
    node_count = text_nodes.count()
    print(f"Total nodes found: {node_count}")

    if node_count > 0:
        # Click on the text node to select it
        text_nodes.first.click()
        time.sleep(1)

        # Take screenshot of selected text node
        page.screenshot(
            path="D:\\个人项目\\pp\\infinite-canvas\\test_c_text_node_selected.png",
            full_page=True,
        )

        # Check for scrollbars within the node
        # Look for elements with overflow: auto or overflow: scroll
        has_scrollbar = False

        # Check the node itself
        node = text_nodes.first
        overflow = node.evaluate("el => window.getComputedStyle(el).overflow")
        overflow_y = node.evaluate("el => window.getComputedStyle(el).overflowY")
        print(f"Node overflow: {overflow}, overflowY: {overflow_y}")

        if (
            "scroll" in overflow
            or "scroll" in overflow_y
            or "auto" in overflow
            or "auto" in overflow_y
        ):
            has_scrollbar = True

        # Check child elements
        children = node.locator("*")
        for i in range(children.count()):
            child = children.nth(i)
            if child.is_visible():
                child_overflow = child.evaluate(
                    "el => window.getComputedStyle(el).overflow"
                )
                child_overflow_y = child.evaluate(
                    "el => window.getComputedStyle(el).overflowY"
                )
                if (
                    "scroll" in child_overflow
                    or "scroll" in child_overflow_y
                    or "auto" in child_overflow
                    or "auto" in child_overflow_y
                ):
                    has_scrollbar = True
                    print(
                        f"Child {i} has scrollbar: overflow={child_overflow}, overflowY={child_overflow_y}"
                    )

        passed = not has_scrollbar
    else:
        print("No nodes found to test")
        passed = False
        has_scrollbar = "N/A"

    return {
        "test": "text_node_scrollbar",
        "passed": passed,
        "details": f"Nodes: {node_count}, Has scrollbar: {has_scrollbar}",
        "screenshot": "test_c_text_node_selected.png",
    }


def test_personal_center_settings(page):
    """Test (d): Verify personal center shows OpenRouter settings with three model selectors"""
    print("\n=== Test (d): Personal Center Settings ===")

    page.goto("http://127.0.0.1:5180")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Generate random user credentials
    username, password = generate_random_user()
    print(f"Generated user: {username}")

    # Click on the user/profile button in the bottom toolbar (4th button)
    user_button = page.locator("button").nth(4)  # 0-indexed, so 4th button
    user_button.click()
    time.sleep(1)

    # Take screenshot of user menu
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_d_user_menu.png", full_page=True
    )

    # Look for login/register option
    login_option = page.locator('text="登录"')
    register_option = page.locator('text="注册"')

    if register_option.count() > 0:
        register_option.first.click()
        time.sleep(1)
    elif login_option.count() > 0:
        login_option.first.click()
        time.sleep(1)

    # Take screenshot of login/register form
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_d_auth_form.png", full_page=True
    )

    # Look for registration form fields
    username_input = page.locator(
        'input[placeholder*="用户名"], input[placeholder*="username"], input[type="text"]'
    ).first
    password_input = page.locator(
        'input[placeholder*="密码"], input[placeholder*="password"], input[type="password"]'
    ).first

    if username_input.is_visible() and password_input.is_visible():
        # Fill in registration form
        username_input.fill(username)
        password_input.fill(password)

        # Look for confirm password field
        confirm_password = page.locator(
            'input[placeholder*="确认"], input[placeholder*="confirm"]'
        )
        if confirm_password.count() > 0:
            confirm_password.first.fill(password)

        # Submit form
        submit_button = page.locator(
            'button[type="submit"], button:has-text("注册"), button:has-text("Register")'
        )
        if submit_button.count() > 0:
            submit_button.first.click()
            time.sleep(2)

    # Take screenshot after registration attempt
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_d_after_register.png",
        full_page=True,
    )

    # Now click on user button again to access settings
    user_button = page.locator("button").nth(4)
    user_button.click()
    time.sleep(1)

    # Look for settings option
    settings_option = page.locator('text="设置"')
    if settings_option.count() > 0:
        settings_option.first.click()
        time.sleep(1)

    # Take screenshot of settings page
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_d_settings.png", full_page=True
    )

    # Look for OpenRouter settings
    openrouter_text = page.locator('text="OpenRouter"')
    openrouter_count = openrouter_text.count()
    print(f"OpenRouter references found: {openrouter_count}")

    # Look for model selectors
    model_selectors = page.locator('select, [role="combobox"], [role="listbox"]')
    selector_count = model_selectors.count()
    print(f"Model selectors found: {selector_count}")

    # Look for text/image/video specific selectors
    text_model = page.locator('text="文本模型"')
    image_model = page.locator('text="图片模型"')
    video_model = page.locator('text="视频模型"')

    text_count = text_model.count()
    image_count = image_model.count()
    video_count = video_model.count()

    print(f"Text model selectors: {text_count}")
    print(f"Image model selectors: {image_count}")
    print(f"Video model selectors: {video_count}")

    # Check if we have three separate selectors
    has_three_selectors = (
        text_count > 0 and image_count > 0 and video_count > 0
    ) or selector_count >= 3

    passed = openrouter_count > 0 and has_three_selectors

    return {
        "test": "personal_center_settings",
        "passed": passed,
        "details": f"OpenRouter refs: {openrouter_count}, Selectors: {selector_count}, Text: {text_count}, Image: {image_count}, Video: {video_count}",
        "screenshot": "test_d_settings.png",
    }


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        results = []

        try:
            # Test (a): Blank canvas
            result_a = test_blank_canvas(page)
            results.append(result_a)

            # Test (b): Image node controls
            result_b = test_image_node_controls(page)
            results.append(result_b)

            # Test (c): Text node scrollbar
            result_c = test_text_node_scrollbar(page)
            results.append(result_c)

            # Test (d): Personal center settings
            result_d = test_personal_center_settings(page)
            results.append(result_d)

        except Exception as e:
            print(f"Error during testing: {e}")
            import traceback

            traceback.print_exc()

        finally:
            browser.close()

        # Print summary
        print("\n" + "=" * 50)
        print("QA TEST SUMMARY")
        print("=" * 50)

        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"\n{result['test'].upper()}: {status}")
            print(f"  Details: {result['details']}")
            print(f"  Screenshot: {result['screenshot']}")

        # Overall result
        all_passed = all(r["passed"] for r in results)
        print(f"\nOVERALL: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

        return results


if __name__ == "__main__":
    main()

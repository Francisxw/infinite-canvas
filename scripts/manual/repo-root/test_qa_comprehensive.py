from playwright.sync_api import sync_playwright
import time
import random
import string


def generate_random_user():
    """Generate random user credentials for testing"""
    username = "testuser_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=8)
    )
    email = username + "@example.com"
    password = "TestPass123!"
    return username, email, password


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

    # Click on the "新建节点" (New Node) button in the bottom toolbar
    # This is the first button with the Plus icon
    new_node_button = page.locator('button[aria-label="新建节点"]')
    if new_node_button.count() > 0:
        print("Clicking '新建节点' button...")
        new_node_button.click()
        time.sleep(1)

        # Take screenshot to see the create panel
        page.screenshot(
            path="D:\\个人项目\\pp\\infinite-canvas\\test_b_create_panel.png",
            full_page=True,
        )

        # Look for the "图片" (Image) button in the create panel
        image_button = page.locator('button[data-testid="dock-create-image"]')
        if image_button.count() > 0:
            print("Clicking '图片' button...")
            image_button.click()
            time.sleep(2)
        else:
            # Try alternative selector
            image_button = page.locator('button:has-text("图片")')
            if image_button.count() > 0:
                print("Clicking '图片' button (alternative)...")
                image_button.first.click()
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
        handles_clipped = "N/A"

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

    # Click on the "新建节点" (New Node) button
    new_node_button = page.locator('button[aria-label="新建节点"]')
    if new_node_button.count() > 0:
        print("Clicking '新建节点' button...")
        new_node_button.click()
        time.sleep(1)

        # Look for the "文本" (Text) button in the create panel
        text_button = page.locator('button[data-testid="dock-create-text"]')
        if text_button.count() > 0:
            print("Clicking '文本' button...")
            text_button.click()
            time.sleep(2)
        else:
            # Try alternative selector
            text_button = page.locator('button:has-text("文本")')
            if text_button.count() > 0:
                print("Clicking '文本' button (alternative)...")
                text_button.first.click()
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
    username, email, password = generate_random_user()
    print(f"Generated user: {username}, email: {email}")

    # Click on the "个人中心" (Personal Center) button in the bottom toolbar
    profile_button = page.locator('button[aria-label="个人中心"]')
    if profile_button.count() > 0:
        print("Clicking '个人中心' button...")
        profile_button.click()
        time.sleep(1)

    # Take screenshot of personal center
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_d_personal_center.png",
        full_page=True,
    )

    # Look for registration form
    # First, click on "注册" (Register) tab
    register_tab = page.locator('button:has-text("注册")')
    if register_tab.count() > 0:
        print("Clicking '注册' tab...")
        register_tab.first.click()
        time.sleep(1)

    # Fill in registration form
    display_name_input = page.locator('input[placeholder="输入显示名称"]')
    email_input = page.locator('input[placeholder="name@example.com"]')
    password_input = page.locator('input[placeholder="至少 6 位"]')

    if (
        display_name_input.count() > 0
        and email_input.count() > 0
        and password_input.count() > 0
    ):
        print("Filling registration form...")
        display_name_input.fill(username)
        email_input.fill(email)
        password_input.fill(password)

        # Take screenshot of filled form
        page.screenshot(
            path="D:\\个人项目\\pp\\infinite-canvas\\test_d_registration_form.png",
            full_page=True,
        )

        # Submit form
        submit_button = page.locator('button:has-text("注册并进入账户中心")')
        if submit_button.count() > 0:
            print("Clicking '注册并进入账户中心' button...")
            submit_button.first.click()
            time.sleep(3)

    # Take screenshot after registration
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_d_after_register.png",
        full_page=True,
    )

    # Now check for OpenRouter settings
    # Look for OpenRouter section
    openrouter_section = page.locator('text="OpenRouter 自定义配置"')
    openrouter_count = openrouter_section.count()
    print(f"OpenRouter section found: {openrouter_count}")

    # Look for model selectors
    # There should be three select elements for text, image, and video models
    model_selectors = page.locator("select")
    selector_count = model_selectors.count()
    print(f"Model selectors found: {selector_count}")

    # Look for specific labels
    text_model_label = page.locator('label:has-text("文本默认模型")')
    image_model_label = page.locator('label:has-text("图像默认模型")')
    video_model_label = page.locator('label:has-text("视频默认模型")')

    text_count = text_model_label.count()
    image_count = image_model_label.count()
    video_count = video_model_label.count()

    print(f"Text model label: {text_count}")
    print(f"Image model label: {image_count}")
    print(f"Video model label: {video_count}")

    # Check if we have three separate selectors
    has_three_selectors = (
        text_count > 0 and image_count > 0 and video_count > 0
    ) or selector_count >= 3

    passed = openrouter_count > 0 and has_three_selectors

    return {
        "test": "personal_center_settings",
        "passed": passed,
        "details": f"OpenRouter section: {openrouter_count}, Selectors: {selector_count}, Text label: {text_count}, Image label: {image_count}, Video label: {video_count}",
        "screenshot": "test_d_after_register.png",
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

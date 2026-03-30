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
    time.sleep(2)  # Wait for any animations

    # Take screenshot of initial state
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_blank_canvas.png", full_page=True
    )

    # Check for canvas element
    canvas = page.locator("canvas")
    canvas_count = canvas.count()
    print(f"Canvas elements found: {canvas_count}")

    # Check if there are any nodes on the canvas
    # Look for common node indicators
    nodes = page.locator('[class*="node"], [class*="Node"], [data-testid*="node"]')
    node_count = nodes.count()
    print(f"Node elements found: {node_count}")

    # Check for any visible text that might indicate pre-loaded content
    visible_text = page.locator(
        "text=/^(?!.*(?:login|register|sign|canvas|infinite)).*$/i"
    )

    # Check if canvas area is empty (no nodes)
    is_blank = node_count == 0

    return {
        "test": "blank_canvas",
        "passed": is_blank,
        "details": f"Canvas elements: {canvas_count}, Node elements: {node_count}",
        "screenshot": "test_blank_canvas.png",
    }


def test_image_node_controls(page):
    """Test (b): Verify image node left/right + controls are visible and not clipped"""
    print("\n=== Test (b): Image Node Controls ===")

    # First, we need to create an image node
    # Look for image node creation button or menu
    page.goto("http://127.0.0.1:5180")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Try to find and click on canvas to create a node
    # Look for toolbar or menu to add image node
    add_button = page.locator(
        'button:has-text("Add"), button:has-text("Create"), button:has-text("+"), [class*="add"], [class*="create"]'
    )

    if add_button.count() > 0:
        add_button.first.click()
        time.sleep(1)

    # Look for image node option
    image_option = page.locator('button:has-text("Image")')

    if image_option.count() > 0:
        image_option.first.click()
        time.sleep(1)

    # Alternative: Try right-click context menu
    page.mouse.click(400, 300, button="right")
    time.sleep(1)

    # Take screenshot to see current state
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_image_node_1.png", full_page=True
    )

    # Look for any node that might be created
    nodes = page.locator('[class*="node"], [class*="Node"]')

    if nodes.count() > 0:
        # Click on the first node to select it
        nodes.first.click()
        time.sleep(1)

        # Take screenshot of selected node
        page.screenshot(
            path="D:\\个人项目\\pp\\infinite-canvas\\test_image_node_2.png",
            full_page=True,
        )

        # Check for control points/handles
        controls = page.locator(
            '[class*="handle"], [class*="control"], [class*="port"], [class*="Port"]'
        )
        control_count = controls.count()
        print(f"Control elements found: {control_count}")

        # Check if controls are visible (not clipped)
        visible_controls = 0
        for i in range(control_count):
            control = controls.nth(i)
            if control.is_visible():
                visible_controls += 1

        print(f"Visible controls: {visible_controls}")

        # Check for left/right specific controls
        left_controls = page.locator(
            '[class*="left"], [class*="Left"], [data-position="left"]'
        )
        right_controls = page.locator(
            '[class*="right"], [class*="Right"], [data-position="right"]'
        )

        left_count = left_controls.count()
        right_count = right_controls.count()
        print(f"Left controls: {left_count}, Right controls: {right_count}")

        passed = visible_controls > 0 and (left_count > 0 or right_count > 0)
    else:
        print("No nodes found to test")
        passed = False

    return {
        "test": "image_node_controls",
        "passed": passed,
        "details": f"Controls found: {control_count}, Visible: {visible_controls}, Left: {left_count}, Right: {right_count}",
        "screenshot": "test_image_node_2.png",
    }


def test_text_node_scrollbar(page):
    """Test (c): Verify text node initial display has no unnecessary scrollbar"""
    print("\n=== Test (c): Text Node Scrollbar ===")

    page.goto("http://127.0.0.1:5180")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Try to create a text node
    # Look for text node creation option
    add_button = page.locator(
        'button:has-text("Add"), button:has-text("Create"), button:has-text("+"), [class*="add"], [class*="create"]'
    )

    if add_button.count() > 0:
        add_button.first.click()
        time.sleep(1)

    # Look for text node option
    text_option = page.locator('button:has-text("Text")')

    if text_option.count() > 0:
        text_option.first.click()
        time.sleep(1)

    # Alternative: Try double-click to create text node
    page.mouse.dblclick(400, 300)
    time.sleep(1)

    # Take screenshot
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_text_node_1.png", full_page=True
    )

    # Look for text nodes
    text_nodes = page.locator(
        '[class*="text"], [class*="Text"], textarea, [contenteditable="true"]'
    )

    if text_nodes.count() > 0:
        # Check for scrollbars
        scrollbar_elements = page.locator(
            '[class*="scroll"], [style*="overflow: auto"], [style*="overflow: scroll"]'
        )
        scrollbar_count = scrollbar_elements.count()
        print(f"Scrollbar elements found: {scrollbar_count}")

        # Check if any text node has scrollbar visible
        has_scrollbar = False
        for i in range(text_nodes.count()):
            node = text_nodes.nth(i)
            if node.is_visible():
                # Check computed style for overflow
                overflow = node.evaluate("el => window.getComputedStyle(el).overflow")
                overflow_y = node.evaluate(
                    "el => window.getComputedStyle(el).overflowY"
                )
                print(f"Text node {i}: overflow={overflow}, overflowY={overflow_y}")

                if (
                    "scroll" in overflow
                    or "scroll" in overflow_y
                    or "auto" in overflow
                    or "auto" in overflow_y
                ):
                    has_scrollbar = True

        passed = not has_scrollbar
    else:
        print("No text nodes found")
        passed = False

    return {
        "test": "text_node_scrollbar",
        "passed": passed,
        "details": f"Text nodes found: {text_nodes.count()}, Has scrollbar: {has_scrollbar if text_nodes.count() > 0 else 'N/A'}",
        "screenshot": "test_text_node_1.png",
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

    # Look for login/register button
    login_button = page.locator(
        'button:has-text("Login"), button:has-text("Sign In"), a:has-text("Login"), [class*="login"]'
    )
    register_button = page.locator(
        'button:has-text("Register"), button:has-text("Sign Up"), a:has-text("Register"), [class*="register"]'
    )

    # Try to register first
    if register_button.count() > 0:
        register_button.first.click()
        time.sleep(1)
    elif login_button.count() > 0:
        login_button.first.click()
        time.sleep(1)

    # Take screenshot of login/register form
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_auth_1.png", full_page=True
    )

    # Look for registration form
    username_input = page.locator(
        'input[name="username"], input[placeholder*="username"], input[type="text"]'
    ).first
    password_input = page.locator(
        'input[name="password"], input[placeholder*="password"], input[type="password"]'
    ).first

    if username_input.is_visible() and password_input.is_visible():
        # Fill in registration form
        username_input.fill(username)
        password_input.fill(password)

        # Look for confirm password field
        confirm_password = page.locator(
            'input[name="confirm_password"], input[placeholder*="confirm"]'
        )
        if confirm_password.count() > 0:
            confirm_password.first.fill(password)

        # Submit form
        submit_button = page.locator(
            'button[type="submit"], button:has-text("Register"), button:has-text("Sign Up"), button:has-text("Create")'
        )
        if submit_button.count() > 0:
            submit_button.first.click()
            time.sleep(2)

    # Take screenshot after registration attempt
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_auth_2.png", full_page=True
    )

    # Now look for personal center or settings
    # Try different approaches to access settings
    settings_button = page.locator(
        'button:has-text("Settings"), a:has-text("Settings"), [class*="settings"], [href*="settings"]'
    )
    profile_button = page.locator(
        'button:has-text("Profile"), a:has-text("Profile"), [class*="profile"], [href*="profile"]'
    )
    user_menu = page.locator('[class*="user"], [class*="avatar"], [class*="account"]')

    if settings_button.count() > 0:
        settings_button.first.click()
        time.sleep(1)
    elif profile_button.count() > 0:
        profile_button.first.click()
        time.sleep(1)
    elif user_menu.count() > 0:
        user_menu.first.click()
        time.sleep(1)

    # Take screenshot of settings/profile page
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_settings_1.png", full_page=True
    )

    # Look for OpenRouter settings
    openrouter_text = page.locator("text=OpenRouter")
    openrouter_count = openrouter_text.count()
    print(f"OpenRouter references found: {openrouter_count}")

    # Look for model selectors
    model_selectors = page.locator(
        'select, [class*="select"], [role="combobox"], [role="listbox"]'
    )
    selector_count = model_selectors.count()
    print(f"Model selectors found: {selector_count}")

    # Look for text/image/video specific selectors
    text_model = page.locator('label:has-text("Text")')
    image_model = page.locator('label:has-text("Image")')
    video_model = page.locator('label:has-text("Video")')

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
        "screenshot": "test_settings_1.png",
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

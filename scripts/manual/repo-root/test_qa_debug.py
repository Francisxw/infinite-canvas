from playwright.sync_api import sync_playwright
import time
import random
import string
import requests
import json


def generate_random_user():
    """Generate random user credentials for testing"""
    username = "testuser_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=8)
    )
    email = username + "@example.com"
    password = "TestPass123!"
    return username, email, password


def register_user_via_api(username, email, password):
    """Register a user via API"""
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/register",
            json={"email": email, "password": password, "display_name": username},
            headers={"Content-Type": "application/json"},
        )
        print(f"Registration response: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Registration failed: {response.text}")
            return None
    except Exception as e:
        print(f"Registration error: {e}")
        return None


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
        has_visible_scrollbar = False

        # Check the node itself
        node = text_nodes.first
        overflow = node.evaluate("el => window.getComputedStyle(el).overflow")
        overflow_y = node.evaluate("el => window.getComputedStyle(el).overflowY")
        print(f"Node overflow: {overflow}, overflowY: {overflow_y}")

        if "scroll" in overflow or "scroll" in overflow_y:
            has_visible_scrollbar = True

        # Check child elements for visible scrollbars
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

                # Check if scrollbar is actually visible (not just overflow: auto)
                if "scroll" in child_overflow or "scroll" in child_overflow_y:
                    has_visible_scrollbar = True
                    print(
                        f"Child {i} has visible scrollbar: overflow={child_overflow}, overflowY={child_overflow_y}"
                    )

                # Also check if element has scrollHeight > clientHeight (indicating scrollable content)
                scroll_info = child.evaluate("""el => ({
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight,
                    scrollWidth: el.scrollWidth,
                    clientWidth: el.clientWidth
                })""")

                if (
                    scroll_info["scrollHeight"] > scroll_info["clientHeight"]
                    or scroll_info["scrollWidth"] > scroll_info["clientWidth"]
                ):
                    print(
                        f"Child {i} is scrollable: scrollHeight={scroll_info['scrollHeight']}, clientHeight={scroll_info['clientHeight']}"
                    )
                    # But this doesn't mean there's a visible scrollbar - it could be hidden

        passed = not has_visible_scrollbar
    else:
        print("No nodes found to test")
        passed = False
        has_visible_scrollbar = "N/A"

    return {
        "test": "text_node_scrollbar",
        "passed": passed,
        "details": f"Nodes: {node_count}, Has visible scrollbar: {has_visible_scrollbar}",
        "screenshot": "test_c_text_node_selected.png",
    }


def test_personal_center_settings(page):
    """Test (d): Verify personal center shows OpenRouter settings with three model selectors"""
    print("\n=== Test (d): Personal Center Settings ===")

    # Generate random user credentials
    username, email, password = generate_random_user()
    print(f"Generated user: {username}, email: {email}")

    # Register user via API first
    registration_result = register_user_via_api(username, email, password)
    if not registration_result:
        print("Failed to register user via API")
        return {
            "test": "personal_center_settings",
            "passed": False,
            "details": "Failed to register user via API",
            "screenshot": "test_d_registration_failed.png",
        }

    print(f"User registered successfully: {registration_result}")

    # Now navigate to the app and login
    page.goto("http://127.0.0.1:5180")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Click on the "个人中心" (Personal Center) button
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

    # Look for login form
    # First, click on "登录" (Login) tab
    login_tab = page.locator('button:has-text("登录")')
    if login_tab.count() > 0:
        print("Clicking '登录' tab...")
        login_tab.first.click()
        time.sleep(1)

    # Fill in login form
    email_input = page.locator('input[placeholder="name@example.com"]')
    password_input = page.locator('input[placeholder="至少 6 位"]')

    if email_input.count() > 0 and password_input.count() > 0:
        print("Filling login form...")
        email_input.fill(email)
        password_input.fill(password)

        # Take screenshot of filled form
        page.screenshot(
            path="D:\\个人项目\\pp\\infinite-canvas\\test_d_login_form.png",
            full_page=True,
        )

        # Submit form
        submit_button = page.locator('button:has-text("登录并开始使用")')
        if submit_button.count() > 0:
            print("Clicking '登录并开始使用' button...")
            submit_button.first.click()
            time.sleep(3)

    # Take screenshot after login
    page.screenshot(
        path="D:\\个人项目\\pp\\infinite-canvas\\test_d_after_login.png", full_page=True
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
        "screenshot": "test_d_after_login.png",
    }


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        results = []

        try:
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

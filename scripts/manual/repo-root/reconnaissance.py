from playwright.sync_api import sync_playwright
import time
import random
import string


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            # Navigate to the app
            page.goto("http://127.0.0.1:5180")
            page.wait_for_load_state("networkidle")
            time.sleep(3)  # Wait for any animations

            # Take screenshot of initial state
            page.screenshot(
                path="D:\\个人项目\\pp\\infinite-canvas\\initial_state.png",
                full_page=True,
            )

            # Get page content to understand structure
            content = page.content()
            print("Page title:", page.title())

            # Check for overlay elements
            overlays = page.locator(
                '[class*="overlay"], [class*="modal"], [class*="fixed"]'
            )
            print(f"Overlay elements found: {overlays.count()}")

            # Check for canvas
            canvas = page.locator("canvas")
            print(f"Canvas elements: {canvas.count()}")

            # Check for nodes
            nodes = page.locator('[class*="node"]')
            print(f"Node elements: {nodes.count()}")

            # Check for buttons
            buttons = page.locator("button")
            print(f"Button elements: {buttons.count()}")

            # List all buttons
            for i in range(buttons.count()):
                button = buttons.nth(i)
                if button.is_visible():
                    text = button.text_content()
                    print(f"  Button {i}: {text}")

            # Check for any welcome/landing page elements
            welcome = page.locator('text="Welcome"')
            print(f"Welcome elements: {welcome.count()}")

            # Check for login/register
            login = page.locator('text="Login"')
            register = page.locator('text="Register"')
            print(
                f"Login elements: {login.count()}, Register elements: {register.count()}"
            )

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            browser.close()


if __name__ == "__main__":
    main()

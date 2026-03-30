from playwright.sync_api import sync_playwright
import time


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            # Navigate to the app
            page.goto("http://127.0.0.1:5180")
            page.wait_for_load_state("networkidle")
            time.sleep(3)

            # Get all buttons and their properties
            buttons = page.locator("button")
            print(f"Total buttons: {buttons.count()}")

            for i in range(buttons.count()):
                button = buttons.nth(i)
                if button.is_visible():
                    text = button.text_content()
                    classes = button.get_attribute("class")
                    print(f"Button {i}: text='{text}', class='{classes}'")

            # Click the "+" button (first button)
            plus_button = page.locator("button").first
            print(f"\nClicking first button: '{plus_button.text_content()}'")
            plus_button.click()
            time.sleep(2)

            # Take screenshot
            page.screenshot(
                path="D:\\个人项目\\pp\\infinite-canvas\\debug_after_click.png",
                full_page=True,
            )

            # Check for any new elements
            print("\nAfter clicking:")
            all_elements = page.locator("*")
            print(f"Total elements: {all_elements.count()}")

            # Look for menu items
            menu_items = page.locator(
                '[role="menuitem"], [class*="menu-item"], [class*="MenuItem"]'
            )
            print(f"Menu items: {menu_items.count()}")

            # Look for any text containing "图片" or "Image"
            image_text = page.locator('text="图片"')
            print(f"'图片' text elements: {image_text.count()}")

            # Look for any text containing "文本" or "Text"
            text_text = page.locator('text="文本"')
            print(f"'文本' text elements: {text_text.count()}")

            # Get page content
            content = page.content()
            # Save to file for inspection
            with open(
                "D:\\个人项目\\pp\\infinite-canvas\\debug_page_content.html",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(content)

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            browser.close()


if __name__ == "__main__":
    main()

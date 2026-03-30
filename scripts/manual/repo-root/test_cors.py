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
            time.sleep(2)

            # Try to make a request to the backend from the browser context
            result = page.evaluate("""async () => {
                try {
                    const response = await fetch('http://localhost:8000/api/auth/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            email: 'test@example.com',
                            password: 'test123',
                            display_name: 'test'
                        })
                    });
                    return {
                        status: response.status,
                        statusText: response.statusText,
                        ok: response.ok
                    };
                } catch (error) {
                    return {
                        error: error.message,
                        name: error.name
                    };
                }
            }""")

            print(f"Fetch result: {result}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            browser.close()


if __name__ == "__main__":
    main()

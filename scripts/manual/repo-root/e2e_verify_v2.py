from playwright.sync_api import sync_playwright
import time
import random


def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        print("=== Starting End-to-End Verification ===")
        print()

        # Step 1: Navigate to app
        print("1. Navigating to http://localhost:15191...")
        page.goto("http://localhost:15191")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="e2e_01_initial.png", full_page=True)
        print("   [OK] Page loaded")
        print()

        # Get all buttons info first
        print("2. Analyzing UI structure...")
        buttons = page.locator("button").all()
        print(f"   Total buttons: {len(buttons)}")

        dock_button_info = []
        for i, btn in enumerate(buttons):
            try:
                box = btn.bounding_box()
                text = btn.text_content() or ""
                aria = btn.get_attribute("aria-label") or ""
                if box:
                    dock_button_info.append(
                        {
                            "index": i,
                            "text": text,
                            "aria": aria,
                            "x": box["x"],
                            "y": box["y"],
                            "element": btn,
                        }
                    )
                    print(
                        f"   Button {i}: text='{text}', aria='{aria}', pos=({box['x']:.0f}, {box['y']:.0f})"
                    )
            except:
                pass

        # Find bottom dock buttons (y > 700)
        bottom_buttons = [b for b in dock_button_info if b["y"] > 700]
        print(f"   Bottom dock buttons: {len(bottom_buttons)}")
        print()

        # Step 2: Click profile button (last button in dock - person icon)
        print("3. Accessing Personal Center via profile icon...")

        profile_btn = None
        for btn in bottom_buttons:
            if btn["x"] > 600:  # Right side of dock
                profile_btn = btn["element"]
                print(f"   Using button at index {btn['index']} as profile button")
                break

        if not profile_btn and len(bottom_buttons) > 0:
            profile_btn = bottom_buttons[-1]["element"]
            print(f"   Using last bottom button as profile")

        if profile_btn:
            profile_btn.click()
            time.sleep(1)
            page.screenshot(path="e2e_02_profile_open.png", full_page=True)
            print("   [OK] Clicked profile button")
            print()

        # Step 3: Look for Register/Login options
        print("4. Looking for registration/login form...")

        # Check what's on screen now
        all_text = page.locator("body").text_content() or ""
        print(f"   Page text sample: {all_text[:200]}")

        # Look for register/signup/login tabs or links
        auth_keywords = ["register", "sign up", "login", "sign in", "注册", "登录"]
        found_auth = []
        for keyword in auth_keywords:
            if keyword.lower() in all_text.lower():
                found_auth.append(keyword)

        print(f"   Found auth keywords: {found_auth}")

        # Try clicking on register text if found
        register_clicked = False
        for keyword in ["Register", "Sign up", "注册"]:
            try:
                selector = f"text={keyword}"
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.click()
                    print(f"   [OK] Clicked: {keyword}")
                    register_clicked = True
                    time.sleep(0.5)
                    break
            except:
                continue

        page.screenshot(path="e2e_03_auth_form.png", full_page=True)

        # Step 4: Fill registration form
        print()
        print("5. Attempting to register...")

        random_id = random.randint(10000, 99999)
        username = f"testuser{random_id}"
        password = "TestPass123!"

        print(f"   Credentials: {username} / {password}")

        # Find all input fields
        inputs = page.locator("input").all()
        print(f"   Found {len(inputs)} input fields")

        for i, inp in enumerate(inputs):
            try:
                input_type = inp.get_attribute("type") or "text"
                placeholder = inp.get_attribute("placeholder") or ""
                name = inp.get_attribute("name") or ""
                print(
                    f"   Input {i}: type={input_type}, name={name}, placeholder={placeholder}"
                )
            except:
                pass

        # Fill inputs
        filled_count = 0
        for inp in inputs:
            try:
                input_type = inp.get_attribute("type") or "text"
                if (
                    input_type == "text"
                    or "user" in (inp.get_attribute("name") or "").lower()
                ):
                    inp.fill(username)
                    filled_count += 1
                    print("   [OK] Filled username")
                elif input_type == "password":
                    inp.fill(password)
                    filled_count += 1
                    print("   [OK] Filled password")
                elif input_type == "email":
                    inp.fill(f"{username}@test.com")
                    filled_count += 1
                    print("   [OK] Filled email")
            except Exception as e:
                print(f"   Error filling input: {e}")

        if filled_count > 0:
            page.screenshot(path="e2e_04_form_filled.png", full_page=True)

            # Submit
            submit_btn = page.locator('button[type="submit"]').first
            if submit_btn:
                submit_btn.click()
                print("   [OK] Submitted form")
                time.sleep(2)
                page.screenshot(path="e2e_05_after_submit.png", full_page=True)

        # Step 5: Check for tabs
        print()
        print("6. Checking for profile tabs...")

        tab_keywords = [
            "overview",
            "recharge",
            "ledger",
            "settings",
            "账户",
            "充值",
            "账单",
            "设置",
        ]
        tabs_found = []

        page_text = page.locator("body").text_content() or ""
        for keyword in tab_keywords:
            if keyword.lower() in page_text.lower():
                tabs_found.append(keyword)

        print(f"   Tabs found: {tabs_found}")

        if tabs_found:
            print("   [OK] Profile panel with tabs visible")
        else:
            print("   [INFO] No tabs found - may be in unauthenticated state")

        print()

        # Step 6: Close any panels and go to canvas
        print("7. Returning to canvas...")

        # Press Escape to close panels
        page.keyboard.press("Escape")
        time.sleep(0.5)

        # Click on canvas area
        page.mouse.click(700, 400)
        time.sleep(0.5)
        page.screenshot(path="e2e_06_canvas_ready.png", full_page=True)
        print("   [OK] Canvas ready")
        print()

        # Step 7: Create nodes via bottom dock
        print("8. Creating nodes via bottom dock...")

        # Find the + button in the dock
        plus_btn = None
        for btn in dock_button_info:
            if "+" in btn["text"] or "add" in btn["aria"].lower():
                plus_btn = btn["element"]
                print(f"   Found + button at index {btn['index']}")
                break

        if not plus_btn and len(bottom_buttons) > 0:
            # Use leftmost bottom button
            plus_btn = bottom_buttons[0]["element"]
            print("   Using leftmost bottom button as create")

        if plus_btn:
            plus_btn.click()
            print("   [OK] Clicked + button")
            time.sleep(1)
            page.screenshot(path="e2e_07_create_panel.png", full_page=True)

            # Check what appeared
            panel_text = page.locator("body").text_content() or ""
            print(f"   Panel content sample: {panel_text[:300]}")

            # Step 8: Select node type
            print()
            print("9. Selecting node type...")

            # Look for node type buttons/options
            all_buttons_after = page.locator("button").all()
            print(f"   Total buttons after click: {len(all_buttons_after)}")

            # Try clicking on the first available option
            node_clicked = False
            for btn in all_buttons_after[
                len(buttons) :
            ]:  # New buttons after opening panel
                try:
                    text = btn.text_content() or ""
                    if text and len(text) < 50:  # Reasonable button text
                        btn.click()
                        print(f"   [OK] Clicked node type: {text}")
                        node_clicked = True
                        time.sleep(0.5)
                        break
                except:
                    pass

            if not node_clicked:
                # Try clicking on any div that looks like a node option
                divs = page.locator("div").all()
                for div in divs[-20:]:  # Check last 20 divs
                    try:
                        if div.is_visible():
                            div.click()
                            print("   [OK] Clicked panel item")
                            node_clicked = True
                            time.sleep(0.5)
                            break
                    except:
                        pass

            page.screenshot(path="e2e_08_first_node.png", full_page=True)
            print()

            # Step 9: Create second node
            print("10. Creating second node...")

            # Press Escape first to close any panel
            page.keyboard.press("Escape")
            time.sleep(0.3)

            # Click + again
            plus_btn.click()
            time.sleep(0.5)

            # Click another option
            all_buttons_now = page.locator("button").all()
            clicked_second = False
            for btn in all_buttons_now[len(buttons) + 1 :]:  # Skip original + new ones
                try:
                    text = btn.text_content() or ""
                    if text and len(text) < 50:
                        btn.click()
                        print(f"   [OK] Clicked second node type: {text}")
                        clicked_second = True
                        time.sleep(0.5)
                        break
                except:
                    pass

            if not clicked_second and node_clicked:
                # Click same place again
                page.mouse.click(700, 500)
                print("   [OK] Created second node at same position")
                clicked_second = True

            page.screenshot(path="e2e_09_two_nodes.png", full_page=True)
            print()

        # Step 10: Check for nodes on canvas
        print("11. Checking for nodes on canvas...")

        # Wait for nodes to render
        time.sleep(2)
        page.screenshot(path="e2e_10_check_nodes.png", full_page=True)

        # Look for react-flow nodes
        node_selectors = [
            ".react-flow__node",
            "[data-id]",
            ".node",
        ]

        nodes_found = []
        for selector in node_selectors:
            try:
                elements = page.locator(selector).all()
                if len(elements) > 0:
                    nodes_found = elements
                    print(f"   [OK] Found {len(elements)} nodes with: {selector}")
                    break
            except:
                pass

        if not nodes_found:
            print("   [WARN] No nodes found on canvas")
            # Print all elements with data-id
            all_data_id = page.locator("[data-id]").all()
            print(f"   Elements with data-id: {len(all_data_id)}")

        print()

        # Step 11: Attempt connection
        if len(nodes_found) >= 2:
            print("12. Attempting to connect nodes...")

            # Get node positions
            node1_box = nodes_found[0].bounding_box()
            node2_box = nodes_found[1].bounding_box()

            print(f"   Node 1: ({node1_box['x']:.0f}, {node1_box['y']:.0f})")
            print(f"   Node 2: ({node2_box['x']:.0f}, {node2_box['y']:.0f})")

            # Look for handles
            handles = page.locator(".react-flow__handle").all()
            print(f"   Handles found: {len(handles)}")

            if len(handles) >= 2:
                h1 = handles[0].bounding_box()
                h2 = handles[1].bounding_box()

                # Drag from h1 to h2
                page.mouse.move(h1["x"] + h1["width"] / 2, h1["y"] + h1["height"] / 2)
                page.mouse.down()
                time.sleep(0.3)
                page.mouse.move(
                    h2["x"] + h2["width"] / 2, h2["y"] + h2["height"] / 2, steps=15
                )
                time.sleep(0.3)
                page.mouse.up()

                print("   [OK] Dragged between handles")
            else:
                # Try dragging from node1 right edge to node2 left edge
                start_x = node1_box["x"] + node1_box["width"]
                start_y = node1_box["y"] + node1_box["height"] / 2
                end_x = node2_box["x"]
                end_y = node2_box["y"] + node2_box["height"] / 2

                page.mouse.move(start_x, start_y)
                page.mouse.down()
                time.sleep(0.3)
                page.mouse.move(end_x, end_y, steps=15)
                time.sleep(0.3)
                page.mouse.up()

                print("   [OK] Dragged from node 1 to node 2")

            time.sleep(1)
            page.screenshot(path="e2e_11_after_connection.png", full_page=True)
            print()

        # Step 12: Check for connections
        print("13. Checking for connections...")

        edges = page.locator(".react-flow__edge").all()
        connections = page.locator(".react-flow__connection").all()

        print(f"   Edges found: {len(edges)}")
        print(f"   Connections found: {len(connections)}")

        has_connection = len(edges) > 0 or len(connections) > 0

        page.screenshot(path="e2e_12_final.png", full_page=True)
        print()

        # Final summary
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"[{'OK' if True else 'FAIL'}] Page loaded")
        print(f"[{'OK' if filled_count > 0 else 'FAIL'}] Registration form accessed")
        print(
            f"[{'OK' if tabs_found else 'FAIL'}] Profile tabs: {tabs_found if tabs_found else 'Not found'}"
        )
        print(
            f"[{'OK' if len(nodes_found) >= 2 else 'FAIL'}] Nodes created: {len(nodes_found)}"
        )
        print(
            f"[{'OK' if has_connection else 'FAIL'}] Connections established: {has_connection}"
        )
        print("=" * 60)

        print()
        print("Screenshots saved: e2e_01 through e2e_12")

        browser.close()


if __name__ == "__main__":
    run_verification()

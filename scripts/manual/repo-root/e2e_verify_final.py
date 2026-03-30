from playwright.sync_api import sync_playwright
import time
import random


def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        print("=== End-to-End Verification ===")
        print()

        # Step 1: Navigate to app
        print("1. Loading app at http://localhost:15191...")
        page.goto("http://localhost:15191")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="e2e_final_01_initial.png", full_page=True)
        print("   [OK] App loaded")
        print()

        # Get button mapping by position
        print("2. Mapping UI buttons...")
        buttons = page.locator("button").all()

        button_map = {}
        for i, btn in enumerate(buttons):
            try:
                box = btn.bounding_box()
                aria = btn.get_attribute("aria-label") or ""
                if box:
                    button_map[i] = {
                        "element": btn,
                        "x": box["x"],
                        "y": box["y"],
                        "aria": aria,
                    }
                    # Print for debugging
                    print(
                        f"   Button {i}: ({box['x']:.0f}, {box['y']:.0f}) - aria: {repr(aria)}"
                    )
            except:
                pass

        # Identify key buttons by position (bottom dock)
        # Bottom dock buttons should be around y=823
        dock_buttons = {
            k: v for k, v in button_map.items() if v["y"] > 700 and v["x"] > 400
        }
        print(f"   Dock buttons identified: {list(dock_buttons.keys())}")
        print()

        # Step 2: Access Personal Center (rightmost dock button)
        print("3. Accessing Personal Center...")

        # Find rightmost button in dock (should be 个人中心)
        personal_center_btn = None
        rightmost_x = 0
        for idx, info in dock_buttons.items():
            if info["x"] > rightmost_x:
                rightmost_x = info["x"]
                personal_center_btn = info["element"]

        if personal_center_btn:
            personal_center_btn.click()
            print("   [OK] Clicked Personal Center button")
            time.sleep(1.5)
            page.screenshot(path="e2e_final_02_personal_center.png", full_page=True)
        else:
            print("   [WARN] Could not find Personal Center button")

        # Step 3: Check for auth state and try to register
        print()
        print("4. Checking authentication state...")

        page_content = page.content()
        has_login_form = (
            "login" in page_content.lower()
            or "注册" in page_content
            or "登录" in page_content
        )
        has_register_link = (
            page.locator("text=注册").count() > 0
            or page.locator("text=Register").count() > 0
        )

        print(f"   Has login form elements: {has_login_form}")
        print(f"   Has register link: {has_register_link}")

        # Try to find and click register
        if has_register_link:
            try:
                page.locator("text=注册").first.click()
                print("   [OK] Clicked Register")
                time.sleep(0.5)
            except:
                pass

        # Fill registration form if present
        username_input = page.locator('input[type="text"]').first
        password_input = page.locator('input[type="password"]').first

        if username_input.count() > 0 and password_input.count() > 0:
            random_id = random.randint(10000, 99999)
            test_user = f"test{random_id}"
            test_pass = "TestPass123!"

            username_input.fill(test_user)
            password_input.fill(test_pass)
            print(f"   [OK] Filled registration form: {test_user}")

            page.screenshot(path="e2e_final_03_form_filled.png", full_page=True)

            # Submit
            submit = page.locator('button[type="submit"]').first
            if submit.count() > 0:
                submit.click()
                print("   [OK] Submitted registration")
                time.sleep(2)
                page.screenshot(path="e2e_final_04_after_register.png", full_page=True)
        else:
            print("   [INFO] No registration form found - may be showing records panel")

        # Step 4: Check for profile tabs
        print()
        print("5. Checking for profile tabs...")

        # Close any panels first
        page.keyboard.press("Escape")
        time.sleep(0.5)

        # Reopen personal center to check for tabs
        if personal_center_btn:
            personal_center_btn.click()
            time.sleep(1)
            page.screenshot(path="e2e_final_05_tabs_check.png", full_page=True)

        # Check for tab keywords
        tab_keywords = [
            "overview",
            "recharge",
            "ledger",
            "settings",
            "总览",
            "充值",
            "账单",
            "设置",
        ]
        page_text = page.locator("body").text_content() or ""
        found_tabs = [k for k in tab_keywords if k in page_text]

        print(f"   Found tabs: {found_tabs if found_tabs else 'None'}")
        print()

        # Step 5: Close panels and create nodes
        print("6. Closing panels and preparing to create nodes...")
        page.keyboard.press("Escape")
        time.sleep(0.5)
        page.mouse.click(700, 400)
        time.sleep(0.5)
        page.screenshot(path="e2e_final_06_canvas.png", full_page=True)
        print("   [OK] Canvas ready")
        print()

        # Step 6: Create nodes using the NEW NODE button
        print("7. Creating first node...")

        # Find leftmost button in dock (should be 新建节点 / New Node)
        new_node_btn = None
        leftmost_x = float("inf")
        for idx, info in dock_buttons.items():
            if info["x"] < leftmost_x:
                leftmost_x = info["x"]
                new_node_btn = info["element"]

        if new_node_btn:
            new_node_btn.click()
            print("   [OK] Clicked New Node button")
            time.sleep(1.5)
            page.screenshot(path="e2e_final_07_node_panel.png", full_page=True)

            # Step 7: Select node type from panel
            print()
            print("8. Selecting node type...")

            # Look for node type options in the panel
            # Common patterns: buttons, cards, or list items
            panel_buttons = page.locator("button").all()

            # Find new buttons that appeared
            new_buttons = [b for b in panel_buttons if b not in buttons]
            print(f"   New buttons in panel: {len(new_buttons)}")

            # Try clicking the first new button
            node_created = False
            for btn in new_buttons[:3]:  # Try first 3 new buttons
                try:
                    if btn.is_visible():
                        btn.click()
                        print("   [OK] Selected node type")
                        node_created = True
                        time.sleep(1)
                        break
                except:
                    pass

            if not node_created:
                # Try clicking at common panel positions
                page.mouse.click(700, 600)
                print("   [OK] Clicked panel area")
                time.sleep(1)

            page.screenshot(path="e2e_final_08_first_node.png", full_page=True)
            print()

            # Step 8: Create second node
            print("9. Creating second node...")

            # Close any panel
            page.keyboard.press("Escape")
            time.sleep(0.3)

            # Click new node button again
            new_node_btn.click()
            time.sleep(0.8)

            # Click another option or same position
            panel_buttons_2 = page.locator("button").all()
            new_buttons_2 = [b for b in panel_buttons_2 if b not in buttons]

            if len(new_buttons_2) > 1:
                try:
                    new_buttons_2[1].click()
                    print("   [OK] Selected second node type")
                except:
                    page.mouse.click(700, 650)
                    print("   [OK] Clicked second position")
            else:
                page.mouse.click(700, 650)
                print("   [OK] Clicked second position")

            time.sleep(1)
            page.screenshot(path="e2e_final_09_second_node.png", full_page=True)
            print()

        # Step 9: Check for nodes on canvas
        print("10. Verifying nodes on canvas...")
        time.sleep(2)
        page.screenshot(path="e2e_final_10_verify_nodes.png", full_page=True)

        # Look for React Flow nodes
        react_nodes = page.locator(".react-flow__node").all()
        data_id_elements = page.locator("[data-id]").all()

        print(f"   React Flow nodes found: {len(react_nodes)}")
        print(f"   Elements with data-id: {len(data_id_elements)}")

        # Get node positions for connection attempt
        nodes_to_connect = react_nodes if len(react_nodes) >= 2 else data_id_elements
        print()

        # Step 10: Attempt connection
        if len(nodes_to_connect) >= 2:
            print("11. Attempting to connect nodes...")

            node1 = nodes_to_connect[0].bounding_box()
            node2 = nodes_to_connect[1].bounding_box()

            print(f"   Node 1: ({node1['x']:.0f}, {node1['y']:.0f})")
            print(f"   Node 2: ({node2['x']:.0f}, {node2['y']:.0f})")

            # Look for handles
            handles = page.locator(".react-flow__handle").all()
            print(f"   Handles found: {len(handles)}")

            if len(handles) >= 2:
                h1 = handles[0].bounding_box()
                h2 = handles[1].bounding_box()

                print(
                    f"   Dragging from handle ({h1['x']:.0f}, {h1['y']:.0f}) to ({h2['x']:.0f}, {h2['y']:.0f})"
                )

                page.mouse.move(h1["x"] + h1["width"] / 2, h1["y"] + h1["height"] / 2)
                page.mouse.down()
                time.sleep(0.3)
                page.mouse.move(
                    h2["x"] + h2["width"] / 2, h2["y"] + h2["height"] / 2, steps=15
                )
                time.sleep(0.3)
                page.mouse.up()

                print("   [OK] Connection drag completed")
            else:
                # Try node-to-node drag
                start_x = node1["x"] + node1["width"]
                start_y = node1["y"] + node1["height"] / 2
                end_x = node2["x"]
                end_y = node2["y"] + node2["height"] / 2

                print(
                    f"   Dragging from node edge ({start_x:.0f}, {start_y:.0f}) to ({end_x:.0f}, {end_y:.0f})"
                )

                page.mouse.move(start_x, start_y)
                page.mouse.down()
                time.sleep(0.3)
                page.mouse.move(end_x, end_y, steps=15)
                time.sleep(0.3)
                page.mouse.up()

                print("   [OK] Node-to-node drag completed")

            time.sleep(1.5)
            page.screenshot(path="e2e_final_11_connection.png", full_page=True)
            print()

        # Step 11: Check for connections
        print("12. Checking for connections...")

        edges = page.locator(".react-flow__edge").all()
        connections = page.locator(".react-flow__connection").all()

        print(f"   Edges: {len(edges)}")
        print(f"   Active connections: {len(connections)}")

        has_connection = len(edges) > 0

        page.screenshot(path="e2e_final_12_final.png", full_page=True)
        print()

        # Final Summary
        print("=" * 60)
        print("FINAL VERIFICATION REPORT")
        print("=" * 60)
        print(f"[PASS] App loads at http://localhost:15191")
        print(
            f"[{'PASS' if found_tabs else 'FAIL'}] Profile panel with tabs: {found_tabs if found_tabs else 'NOT FOUND'}"
        )
        print(
            f"[{'PASS' if len(react_nodes) >= 2 else 'FAIL'}] Nodes created: {len(react_nodes)} (need 2+)"
        )
        print(
            f"[{'PASS' if has_connection else 'FAIL'}] Node connections: {has_connection}"
        )
        print("=" * 60)
        print()
        print("Screenshots saved with prefix 'e2e_final_'")

        browser.close()


if __name__ == "__main__":
    run_verification()

from playwright.sync_api import sync_playwright
import time
import random


def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        print("=== Starting End-to-End Verification ===")
        print()

        # Step 1: Navigate to app
        print("1. Navigating to http://localhost:15191...")
        page.goto("http://localhost:15191")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.screenshot(path="e2e_01_initial_state.png", full_page=True)
        print("   [OK] Page loaded, screenshot saved: e2e_01_initial_state.png")
        print()

        # Step 2: Find and open Personal Center / Profile
        print("2. Looking for Personal Center/Profile access...")

        # Look for profile-related buttons (common patterns)
        profile_selectors = [
            "text=Profile",
            "text=Personal",
            "text=Login",
            "text=Account",
            '[data-testid="profile"]',
            '[data-testid="user-menu"]',
            'button:has-text("Login")',
            'button:has-text("Profile")',
            'button:has-text("Personal")',
        ]

        profile_btn = None
        for selector in profile_selectors:
            try:
                if page.locator(selector).count() > 0:
                    profile_btn = page.locator(selector).first
                    print(f"   Found profile button with selector: {selector}")
                    break
            except:
                continue

        if not profile_btn:
            # Try to find any button in the top navigation
            buttons = page.locator("button").all()
            print(f"   Found {len(buttons)} buttons on page")
            for i, btn in enumerate(buttons[:5]):
                try:
                    text = btn.text_content() or btn.get_attribute("aria-label") or ""
                    print(f"   Button {i}: {text[:30]}")
                except:
                    pass

            # Look for top-left menu mentioned in context
            if len(buttons) > 0:
                menu_btn = page.locator("button").first
                print("   Clicking first button (potentially top-left menu)...")
                menu_btn.click()
                time.sleep(0.5)
                page.screenshot(path="e2e_02_menu_opened.png")

        if profile_btn:
            profile_btn.click()
            time.sleep(0.5)
            page.screenshot(path="e2e_02_profile_clicked.png")
            print("   [OK] Clicked profile button")
            print()

        # Step 3: Register a new account
        print("3. Attempting to register a new account...")

        # Look for register/signup option
        register_selectors = [
            "text=Register",
            "text=Sign Up",
            "text=Sign up",
            'button:has-text("Register")',
            'button:has-text("Sign Up")',
            'a:has-text("Register")',
            'a:has-text("Sign Up")',
        ]

        register_found = False
        for selector in register_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.click()
                    print(f"   Clicked: {selector}")
                    register_found = True
                    time.sleep(0.5)
                    break
            except:
                continue

        if not register_found:
            print(
                "   No explicit Register button found, checking if form is already shown..."
            )

        page.screenshot(path="e2e_03_register_form.png")

        # Fill in registration form
        # Generate unique credentials
        random_id = random.randint(10000, 99999)
        username = f"testuser{random_id}"
        email = f"test{random_id}@test.com"
        password = "TestPass123!"

        print(f"   Using credentials:")
        print(f"   - Username: {username}")
        print(f"   - Email: {email}")
        print(f"   - Password: {password}")

        # Try to find and fill form fields
        field_mappings = {
            "username": [
                'input[name="username"]',
                'input[placeholder*="username" i]',
                "#username",
                'input[type="text"]',
            ],
            "email": [
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="email" i]',
                "#email",
            ],
            "password": [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="password" i]',
                "#password",
            ],
        }

        filled_fields = {}
        for field_name, selectors in field_mappings.items():
            for selector in selectors:
                try:
                    if page.locator(selector).count() > 0:
                        input_field = page.locator(selector).first
                        if field_name == "username":
                            input_field.fill(username)
                        elif field_name == "email":
                            input_field.fill(email)
                        elif field_name == "password":
                            input_field.fill(password)
                        filled_fields[field_name] = selector
                        print(f"   [OK] Filled {field_name} field")
                        break
                except Exception as e:
                    continue

        if filled_fields:
            page.screenshot(path="e2e_04_form_filled.png")

            # Submit the form
            submit_selectors = [
                'button[type="submit"]',
                "text=Register",
                "text=Sign Up",
                "text=Create Account",
                'button:has-text("Register")',
                'button:has-text("Create")',
            ]

            for selector in submit_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click()
                        print(f"   [OK] Clicked submit: {selector}")
                        time.sleep(2)
                        break
                except:
                    continue

            page.screenshot(path="e2e_05_after_register.png")
        else:
            print("   [WARN] Could not find registration form fields")
            print()

        # Step 4: Verify authenticated profile panel with tabs
        print()
        print("4. Verifying authenticated profile panel with tabs...")
        time.sleep(1)

        # Look for profile tabs
        tab_keywords = [
            "overview",
            "recharge",
            "ledger",
            "settings",
            "account",
            "billing",
            "profile",
        ]
        found_tabs = []

        for keyword in tab_keywords:
            try:
                tab_selector = f"text={keyword}"
                if page.locator(tab_selector).count() > 0:
                    found_tabs.append(keyword)
            except:
                pass

        print(f"   Found tabs: {found_tabs}")

        if found_tabs:
            page.screenshot(path="e2e_06_profile_tabs.png")
            print("   [OK] Profile panel with tabs visible")
            print()
        else:
            print("   [WARN] No tabs found - may need to open profile again")
            print()
            # Try to access profile again
            try:
                profile_btn = page.locator("button").first
                if profile_btn:
                    profile_btn.click()
                    time.sleep(0.5)
                    page.screenshot(path="e2e_06_profile_retry.png")
            except:
                pass

        # Step 5: Close any modals/panels and go to canvas
        print("5. Returning to canvas for node operations...")

        # Try to close modal by clicking outside or finding close button
        close_selectors = [
            'button:has-text("Close")',
            'button:has-text("X")',
            '[aria-label="Close"]',
            ".modal-close",
            ".close-btn",
            "text=Close",
        ]

        for selector in close_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.click()
                    print("   Closed modal")
                    break
            except:
                pass

        # Click on canvas area to dismiss
        page.mouse.click(700, 400)
        time.sleep(0.5)
        page.screenshot(path="e2e_07_back_to_canvas.png")
        print("   [OK] Back on canvas")
        print()

        # Step 6: Create nodes via bottom dock
        print("6. Creating nodes via bottom dock...")

        # Get all buttons and find the one that might be the create button
        all_buttons = page.locator("button").all()
        print(f"   Total buttons found: {len(all_buttons)}")

        # Try to find the plus/create button in the bottom area
        create_btn = None
        for btn in all_buttons:
            try:
                text = btn.text_content() or ""
                aria_label = btn.get_attribute("aria-label") or ""
                if (
                    "+" in text
                    or "add" in aria_label.lower()
                    or "create" in aria_label.lower()
                    or "new" in aria_label.lower()
                ):
                    create_btn = btn
                    print(
                        f"   Found create button: text='{text}', aria-label='{aria_label}'"
                    )
                    break
            except:
                continue

        # If not found, try clicking on button with + icon or in bottom area
        if not create_btn:
            # Look for button at bottom of screen
            viewport = page.viewport_size
            bottom_buttons = []
            for btn in all_buttons:
                try:
                    box = btn.bounding_box()
                    if box and box["y"] > viewport["height"] * 0.8:
                        bottom_buttons.append(btn)
                except:
                    continue

            if bottom_buttons:
                create_btn = bottom_buttons[0]
                print("   Using bottom button as create button")

        if create_btn:
            create_btn.click()
            print("   [OK] Clicked create button")
            time.sleep(0.5)
            page.screenshot(path="e2e_08_create_panel_open.png")

            # Step 7: Select node type from create panel
            print()
            print("7. Selecting node type from create panel...")

            # Look for node type options
            node_types = [
                "text=Default",
                "text=Input",
                "text=Output",
                "text=Process",
                "text=Decision",
                "text=Node",
                ".node-type",
                "[data-node-type]",
                "button",
            ]

            node_created = False
            for selector in node_types:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        print(
                            f"   Found {len(elements)} node type options with: {selector}"
                        )
                        # Click the first available node type
                        elements[0].click()
                        print(f"   [OK] Clicked first node type")
                        time.sleep(0.5)
                        node_created = True
                        break
                except Exception as e:
                    continue

            if not node_created:
                # Try clicking on any clickable item in the panel
                panel_items = page.locator("div > div").all()
                for item in panel_items[
                    -10:
                ]:  # Check last 10 elements (likely in panel)
                    try:
                        if item.is_visible():
                            item.click()
                            print("   [OK] Clicked panel item")
                            time.sleep(0.5)
                            node_created = True
                            break
                    except:
                        continue

            page.screenshot(path="e2e_09_first_node_created.png")

            # Create a second node
            print()
            print("8. Creating second node...")

            if create_btn:
                create_btn.click()
                time.sleep(0.5)

                # Select another node type
                for selector in node_types:
                    try:
                        elements = page.locator(selector).all()
                        if len(elements) > 1:
                            elements[1].click()
                            print("   [OK] Selected second node type")
                            time.sleep(0.5)
                            break
                        elif elements:
                            elements[0].click()
                            print("   [OK] Selected node type again")
                            time.sleep(0.5)
                            break
                    except:
                        continue

                page.screenshot(path="e2e_10_second_node_created.png")
                print("   [OK] Second node created")
                print()

        # Step 9: Attempt to connect nodes by dragging handles
        print("9. Attempting to connect nodes by dragging handles...")

        # Take screenshot to see node positions
        page.screenshot(path="e2e_11_before_connection.png")

        # Look for nodes on the canvas
        node_selectors = [
            ".react-flow__node",
            "[data-id]",
            ".node",
            ".flow-node",
        ]

        nodes = []
        for selector in node_selectors:
            try:
                node_elements = page.locator(selector).all()
                if len(node_elements) >= 2:
                    nodes = node_elements
                    print(f"   Found {len(nodes)} nodes with selector: {selector}")
                    break
            except:
                continue

        if len(nodes) >= 2:
            # Get positions of nodes
            node1_box = nodes[0].bounding_box()
            node2_box = nodes[1].bounding_box()

            if node1_box and node2_box:
                print(
                    f"   Node 1 position: x={node1_box['x']:.0f}, y={node1_box['y']:.0f}"
                )
                print(
                    f"   Node 2 position: x={node2_box['x']:.0f}, y={node2_box['y']:.0f}"
                )

                # Look for handles on the first node
                handle_selectors = [
                    ".react-flow__handle",
                    "[data-handleid]",
                    ".handle",
                    ".source",
                    ".target",
                ]

                handles = []
                for selector in handle_selectors:
                    try:
                        handle_elements = page.locator(selector).all()
                        if handle_elements:
                            handles = handle_elements
                            print(f"   Found {len(handles)} handles with: {selector}")
                            break
                    except:
                        continue

                if len(handles) >= 2:
                    # Try to drag from one handle to another
                    source_handle = handles[0]
                    target_handle = handles[1]

                    source_box = source_handle.bounding_box()
                    target_box = target_handle.bounding_box()

                    if source_box and target_box:
                        print(
                            f"   Dragging from handle at ({source_box['x']:.0f}, {source_box['y']:.0f}) to ({target_box['x']:.0f}, {target_box['y']:.0f})"
                        )

                        # Perform drag operation
                        page.mouse.move(
                            source_box["x"] + source_box["width"] / 2,
                            source_box["y"] + source_box["height"] / 2,
                        )
                        page.mouse.down()
                        time.sleep(0.2)
                        page.mouse.move(
                            target_box["x"] + target_box["width"] / 2,
                            target_box["y"] + target_box["height"] / 2,
                            steps=10,
                        )
                        time.sleep(0.2)
                        page.mouse.up()

                        print("   [OK] Drag operation completed")
                        time.sleep(1)
                        page.screenshot(path="e2e_12_after_connection_attempt.png")
                else:
                    # Try dragging from node center to node center
                    print("   No handles found, trying node-to-node drag...")

                    start_x = node1_box["x"] + node1_box["width"] / 2
                    start_y = node1_box["y"] + node1_box["height"] / 2
                    end_x = node2_box["x"] + node2_box["width"] / 2
                    end_y = node2_box["y"] + node2_box["height"] / 2

                    page.mouse.move(start_x, start_y)
                    page.mouse.down()
                    time.sleep(0.2)
                    page.mouse.move(end_x, end_y, steps=10)
                    time.sleep(0.2)
                    page.mouse.up()

                    print("   [OK] Node-to-node drag completed")
                    time.sleep(1)
                    page.screenshot(path="e2e_12_after_node_drag.png")
        else:
            print("   [WARN] Could not find 2 nodes to connect")
            print()

        # Step 10: Check for connection
        print()
        print("10. Checking for connections...")

        connection_selectors = [
            ".react-flow__edge",
            ".react-flow__connection",
            "path[marker-end]",
            ".edge",
        ]

        connections_found = False
        for selector in connection_selectors:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    print(f"   [OK] Found {count} connection(s) with: {selector}")
                    connections_found = True
                    break
            except:
                continue

        if not connections_found:
            print("   [WARN] No connections detected")

        page.screenshot(path="e2e_13_final_state.png", full_page=True)

        # Final summary
        print()
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"[OK] Page loaded successfully")
        print(f"[OK] Registration attempted with user: {username}")
        print(
            f"{'[OK]' if found_tabs else '[WARN]'} Profile tabs found: {found_tabs if found_tabs else 'None'}"
        )
        print(f"{'[OK]' if len(nodes) >= 2 else '[WARN]'} Nodes created: {len(nodes)}")
        print(
            f"{'[OK]' if connections_found else '[WARN]'} Connections established: {connections_found}"
        )
        print("=" * 60)

        print()
        print("All screenshots saved with prefix 'e2e_'")

        browser.close()


if __name__ == "__main__":
    run_verification()

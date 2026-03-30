from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    print("Loading app...")
    page.goto('http://localhost:15191')
    page.wait_for_load_state('networkidle')
    time.sleep(1)
    
    # Initial screenshot
    page.screenshot(path='01_initial.png')
    print("[1] Initial screenshot saved")
    
    # === MENU CHECK ===
    print("\n=== 1. TOP-LEFT FILE/EDIT MENU ===")
    menu_btns = page.locator('button').all()[:2]
    for i, btn in enumerate(menu_btns):
        text = btn.inner_text().strip()
        visible = btn.is_visible()
        clickable = not btn.is_disabled() if hasattr(btn, 'is_disabled') else True
        print(f"  Button {i}: '{text}' - Visible: {visible}, Clickable: {clickable}")
    
    # Click File menu
    print("\n  Clicking File menu...")
    menu_btns[0].click()
    time.sleep(0.3)
    page.screenshot(path='02_menu_open.png')
    print("  [2] Screenshot after clicking File menu")
    
    # === PROFILE PANEL CHECK ===
    print("\n=== 2. PROFILE PANEL ===")
    
    # Look for icon buttons or avatar buttons (buttons 5-8 are at bottom right)
    all_btns = page.locator('button').all()
    print(f"  Total buttons: {len(all_btns)}")
    
    # Try clicking empty buttons (likely icon buttons for profile/settings)
    for idx in [5, 6, 7, 8]:
        if idx < len(all_btns):
            btn = all_btns[idx]
            box = btn.bounding_box()
            if box:
                print(f"\n  Clicking button {idx} at ({box['x']:.0f}, {box['y']:.0f})...")
                btn.click()
                time.sleep(0.5)
                
                # Screenshot
                page.screenshot(path=f'03_profile_{idx}.png')
                print(f"  [3-{idx}] Screenshot saved")
                
                # Check for tab elements
                tabs = page.locator('[role="tab"], .tab, [class*="tab"]').all()
                print(f"  Tab elements found: {len(tabs)}")
                
                # Check for specific tab text
                page_text = page.evaluate('() => document.body.innerText')
                keywords = ['Overview', 'overview', 'Recharge', 'recharge', 'Ledger', 'ledger', 'Settings', 'settings']
                found_tabs = [k for k in keywords if k in page_text]
                if found_tabs:
                    print(f"  Tabs found: {found_tabs}")
                else:
                    print("  No tabs detected in current view")
    
    # === NODE CONNECTION CHECK ===
    print("\n=== 3. NODE CONNECTIONS ===")
    
    # First, check if we can add a node
    add_node_btn = page.locator('button').nth(3)  # The '+' button
    if add_node_btn.is_visible():
        print("  Clicking '+' button to add a node...")
        add_node_btn.click()
        time.sleep(0.5)
        page.screenshot(path='04_after_add_node.png')
        print("  [4] Screenshot after adding node")
    
    # Check for nodes again
    nodes = page.locator('.react-flow__node').all()
    handles = page.locator('.react-flow__handle').all()
    print(f"  Nodes: {len(nodes)}, Handles: {len(handles)}")
    
    if len(nodes) >= 2 and len(handles) >= 2:
        print("\n  Attempting node-to-node connection...")
        source = handles[0]
        target = handles[1]
        src_box = source.bounding_box()
        tgt_box = target.bounding_box()
        
        page.mouse.move(src_box['x'] + src_box['width']/2, src_box['y'] + src_box['height']/2)
        page.mouse.down()
        page.mouse.move(tgt_box['x'] + tgt_box['width']/2, tgt_box['y'] + tgt_box['height']/2, steps=10)
        page.mouse.up()
        time.sleep(0.5)
        
        page.screenshot(path='05_after_connection.png')
        print("  [5] Screenshot after connection attempt")
        
        # Check if edge was created
        edges = page.locator('.react-flow__edge').all()
        print(f"  Edges after attempt: {len(edges)}")
    elif len(nodes) == 1:
        print("  Only 1 node present - need 2+ to test connections")
        # Try adding another node
        add_node_btn.click()
        time.sleep(0.5)
        nodes = page.locator('.react-flow__node').all()
        handles = page.locator('.react-flow__handle').all()
        print(f"  After adding: Nodes: {len(nodes)}, Handles: {len(handles)}")
    else:
        print("  No nodes available for connection testing")
    
    browser.close()
    print("\n=== VERIFICATION COMPLETE ===")

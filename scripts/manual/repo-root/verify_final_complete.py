from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    print("Loading app...")
    page.goto('http://localhost:15191')
    page.wait_for_load_state('networkidle')
    time.sleep(1)
    
    # === MENU VERIFICATION ===
    print("\n=== 1. TOP-LEFT FILE/EDIT MENU ===")
    menu_btns = page.locator('button').all()[:2]
    
    for i, btn in enumerate(menu_btns):
        text = btn.inner_text().strip()
        print(f"  Button {i}: '{text}' - Visible: {btn.is_visible()}")
    
    # Test interactivity
    print("\n  Testing interactivity...")
    menu_btns[0].click()
    time.sleep(0.3)
    
    # Check if dropdown appeared
    dropdown_items = page.locator('[role="menuitem"], .menu-item').all()
    print(f"  Dropdown items found: {len(dropdown_items)}")
    if len(dropdown_items) > 0:
        print("  [OK] File menu is INTERACTIVE - dropdown appeared")
    else:
        print("  [WARN] No dropdown items detected")
    
    # Press Escape to close menu
    page.keyboard.press('Escape')
    time.sleep(0.3)
    
    # === PROFILE PANEL VERIFICATION ===
    print("\n=== 2. PROFILE PANEL ===")
    
    # Look at the bottom toolbar (4 buttons: +, clock, folder, person)
    toolbar_btns = page.locator('button[class*="inline-flex"]').all()
    print(f"  Bottom toolbar buttons: {len(toolbar_btns)}")
    
    # Click the person/profile icon (last one)
    if len(toolbar_btns) >= 4:
        profile_btn = toolbar_btns[-1]
        print("  Clicking profile button (person icon)...")
        profile_btn.click()
        time.sleep(0.8)
        page.screenshot(path='profile_panel.png')
        print("  Screenshot saved: profile_panel.png")
        
        # Check for tabs by looking at visible elements
        tab_elements = page.locator('[role="tab"], button[class*="tab"], .tab').all()
        print(f"  Tab role elements: {len(tab_elements)}")
        
        # Check page text for tab keywords
        page_text = page.evaluate('() => document.body.innerText')
        keywords = ['Overview', 'Recharge', 'Ledger', 'Settings']
        found = []
        for kw in keywords:
            if kw in page_text:
                found.append(kw)
        
        if found:
            print(f"  [OK] Profile panel tabs found: {found}")
        else:
            print("  [INFO] No standard tabs detected in panel")
            # Print first 500 chars of text to debug
            print(f"  Page text sample: {page_text[:500]}")
    
    # Close any modal
    page.keyboard.press('Escape')
    time.sleep(0.3)
    
    # === NODE CONNECTION VERIFICATION ===
    print("\n=== 3. NODE CONNECTIONS ===")
    
    # Use the '+' in the bottom toolbar (first button) to add nodes
    if len(toolbar_btns) >= 1:
        add_btn = toolbar_btns[0]
        print("  Clicking add node button (+)...")
        add_btn.click()
        time.sleep(0.5)
        
        nodes = page.locator('.react-flow__node').all()
        handles = page.locator('.react-flow__handle').all()
        print(f"  After 1st add: {len(nodes)} nodes, {len(handles)} handles")
        
        if len(nodes) >= 1:
            page.screenshot(path='one_node.png')
            print("  Screenshot saved: one_node.png")
            
            # Add second node
            add_btn.click()
            time.sleep(0.5)
            nodes = page.locator('.react-flow__node').all()
            handles = page.locator('.react-flow__handle').all()
            print(f"  After 2nd add: {len(nodes)} nodes, {len(handles)} handles")
            
            if len(nodes) >= 2:
                page.screenshot(path='two_nodes.png')
                print("  Screenshot saved: two_nodes.png")
                
                if len(handles) >= 2:
                    print("\n  Attempting node-to-node connection...")
                    source = handles[0]
                    target = handles[1]
                    src_box = source.bounding_box()
                    tgt_box = target.bounding_box()
                    
                    if src_box and tgt_box:
                        print(f"    Dragging from ({src_box['x']:.0f}, {src_box['y']:.0f}) to ({tgt_box['x']:.0f}, {tgt_box['y']:.0f})")
                        
                        page.mouse.move(src_box['x'] + src_box['width']/2, src_box['y'] + src_box['height']/2)
                        page.mouse.down()
                        page.mouse.move(tgt_box['x'] + tgt_box['width']/2, tgt_box['y'] + tgt_box['height']/2, steps=10)
                        page.mouse.up()
                        time.sleep(0.5)
                        
                        edges = page.locator('.react-flow__edge').all()
                        print(f"    Edges after connection: {len(edges)}")
                        
                        page.screenshot(path='connection_attempt.png')
                        print("    Screenshot saved: connection_attempt.png")
                        
                        if len(edges) > 0:
                            print("    [OK] Connection created successfully")
                        else:
                            print("    [INFO] No edge visible after connection attempt")
                else:
                    print("  Not enough handles to test connection")
            else:
                print("  Second node not added successfully")
        else:
            print("  Node not added successfully")
    else:
        print("  Add node button not found")
    
    browser.close()
    print("\n=== VERIFICATION COMPLETE ===")

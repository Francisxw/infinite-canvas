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
    print("  [OK] File menu clicked successfully")
    
    # Check if dropdown appeared
    dropdown = page.locator('[role="menu"], [class*="dropdown"], [class*="menu-items"]').first
    if dropdown.is_visible():
        print("  [OK] Dropdown menu is visible after click")
    
    # Press Escape to close any menu
    page.keyboard.press('Escape')
    time.sleep(0.3)
    
    # === PROFILE PANEL VERIFICATION ===
    print("\n=== 2. PROFILE PANEL ===")
    
    # Look at the bottom toolbar buttons
    toolbar_btns = page.locator('button[class*="inline-flex"]').all()
    print(f"  Toolbar buttons found: {len(toolbar_btns)}")
    
    # The last one should be profile/user
    if len(toolbar_btns) > 0:
        profile_btn = toolbar_btns[-1]
        print("  Clicking profile button...")
        profile_btn.click()
        time.sleep(0.8)
        page.screenshot(path='profile_panel.png')
        print("  Screenshot saved: profile_panel.png")
        
        # Check for tabs
        tabs_check = page.evaluate('''() => {
            const keywords = ['Overview', 'overview', 'Recharge', 'recharge', 'Ledger', 'ledger', 'Settings', 'settings'];
            const results = {};
            keywords.forEach(kw => {
                const el = Array.from(document.querySelectorAll('*')).find(e => 
                    e.textContent.includes(kw) && e.children.length <= 3
                );
                results[kw] = el ? {found: true, text: el.textContent.trim().slice(0, 50)} : {found: false};
            });
            return results;
        }''')
        
        print("\n  Tab check:")
        tabs_found = 0
        for kw, result in tabs_check.items():
            if result.get('found'):
                print(f"    [OK] '{kw}' found: '{result['text']}'")
                tabs_found += 1
        if tabs_found == 0:
            print("    No tabs detected")
    
    # Press Escape to close panel
    page.keyboard.press('Escape')
    time.sleep(0.3)
    
    # === NODE CONNECTION VERIFICATION ===
    print("\n=== 3. NODE CONNECTIONS ===")
    
    # First check current state
    nodes = page.locator('.react-flow__node').all()
    handles = page.locator('.react-flow__handle').all()
    print(f"  Current: {len(nodes)} nodes, {len(handles)} handles")
    
    # Try to find and click the '+' button in the bottom toolbar (not the zoom one)
    all_btns = page.locator('button').all()
    add_node_btn = None
    for btn in all_btns:
        try:
            text = btn.inner_text().strip()
            if text == '+' and btn.is_visible():
                box = btn.bounding_box()
                # The add node button should be at bottom center area
                if box and box['y'] > 700:
                    add_node_btn = btn
                    break
        except:
            continue
    
    if add_node_btn:
        print("  Clicking add node button...")
        add_node_btn.click()
        time.sleep(0.5)
        
        # Check for nodes again
        nodes = page.locator('.react-flow__node').all()
        handles = page.locator('.react-flow__handle').all()
        print(f"  After add: {len(nodes)} nodes, {len(handles)} handles")
        
        if len(nodes) >= 1:
            page.screenshot(path='node_added.png')
            print("  Screenshot saved: node_added.png")
        
        # Add second node if needed
        if len(nodes) < 2:
            add_node_btn.click()
            time.sleep(0.5)
            nodes = page.locator('.react-flow__node').all()
            handles = page.locator('.react-flow__handle').all()
            print(f"  After 2nd add: {len(nodes)} nodes, {len(handles)} handles")
        
        # Try connection if we have 2+ nodes and 2+ handles
        if len(nodes) >= 2 and len(handles) >= 2:
            print("\n  Attempting node-to-node connection...")
            source = handles[0]
            target = handles[1]
            src_box = source.bounding_box()
            tgt_box = target.bounding_box()
            
            if src_box and tgt_box:
                # Drag from source handle to target handle
                page.mouse.move(src_box['x'] + src_box['width']/2, src_box['y'] + src_box['height']/2)
                page.mouse.down()
                page.mouse.move(tgt_box['x'] + tgt_box['width']/2, tgt_box['y'] + tgt_box['height']/2, steps=10)
                page.mouse.up()
                time.sleep(0.5)
                
                # Check if edge was created
                edges = page.locator('.react-flow__edge').all()
                print(f"  Edges after connection: {len(edges)}")
                
                page.screenshot(path='connection_attempt.png')
                print("  Screenshot saved: connection_attempt.png")
                
                if len(edges) > 0:
                    print("  [OK] Connection appears to have been created")
                else:
                    print("  [INFO] No edge detected after connection attempt")
        else:
            print("  Cannot test connections - insufficient nodes/handles")
    else:
        print("  Add node button not found")
    
    browser.close()
    print("\n=== VERIFICATION COMPLETE ===")

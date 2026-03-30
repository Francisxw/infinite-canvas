from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    print("Loading app...")
    page.goto('http://localhost:15191')
    page.wait_for_load_state('networkidle')
    time.sleep(1)
    
    # Check title
    print(f"Page Title: {page.title()}")
    
    # Check top-left menu
    print("\n=== TOP-LEFT MENU CHECK ===")
    all_btns = page.locator('button').all()
    top_left_btns = []
    for i, btn in enumerate(all_btns[:10]):
        try:
            if btn.is_visible():
                box = btn.bounding_box()
                if box and box.get('top', 999) < 100 and box.get('left', 999) < 300:
                    text = btn.inner_text().strip()
                    top_left_btns.append((i, btn, box, text))
        except:
            continue
    
    print(f"Found {len(top_left_btns)} buttons in top-left area:")
    for idx, btn, box, text in top_left_btns:
        print(f"  Button {idx}: '{text}' at ({box['left']:.0f}, {box['top']:.0f})")
    
    # Click first menu button
    if len(top_left_btns) >= 1:
        idx, btn, _, _ = top_left_btns[0]
        print(f"\nClicking first menu button (index {idx}) to test interactivity...")
        btn.click()
        time.sleep(0.3)
        print("Menu button clicked successfully (interactive)")
    
    # Look for profile/avatar buttons in top-right
    print("\n=== PROFILE PANEL CHECK ===")
    all_btns = page.locator('button').all()
    top_right_btns = []
    for i, btn in enumerate(all_btns):
        try:
            if btn.is_visible():
                box = btn.bounding_box()
                if box and box.get('top', 999) < 100 and box.get('left', 0) > 1000:
                    text = btn.inner_text().strip()[:30]
                    top_right_btns.append((i, btn, box, text))
        except:
            continue
    
    print(f"Found {len(top_right_btns)} buttons in top-right area:")
    for idx, btn, box, text in top_right_btns:
        print(f"  Button {idx}: '{text}' at ({box['left']:.0f}, {box['top']:.0f})")
    
    # Try clicking the last button (likely profile)
    if len(top_right_btns) > 0:
        idx, btn, _, _ = top_right_btns[-1]
        print(f"\nClicking top-right button (index {idx}) to open profile...")
        btn.click()
        time.sleep(0.8)
        
        # Check for tab text in page content
        page_text = page.inner_text('body')
        print("\nTab check in page content:")
        tabs = ['Overview', 'overview', 'Recharge', 'recharge', 'Ledger', 'ledger', 'Settings', 'settings']
        found_any = False
        for tab in tabs:
            if tab in page_text:
                print(f"  [OK] Tab '{tab}' found in page text")
                found_any = True
        if not found_any:
            print("  No tabs found in current page text")
    else:
        print("No top-right buttons found")
    
    # Check nodes and handles
    print("\n=== NODES & CONNECTIONS CHECK ===")
    nodes = page.locator('.react-flow__node').all()
    handles = page.locator('.react-flow__handle').all()
    print(f"React Flow nodes: {len(nodes)}")
    print(f"Connection handles: {len(handles)}")
    
    if len(nodes) >= 2 and len(handles) >= 2:
        print("\nAttempting node-to-node connection...")
        source = handles[0]
        target = handles[1]
        src_box = source.bounding_box()
        tgt_box = target.bounding_box()
        
        if src_box and tgt_box:
            print(f"Dragging from ({src_box['x']:.0f}, {src_box['y']:.0f}) to ({tgt_box['x']:.0f}, {tgt_box['y']:.0f})")
            
            page.mouse.move(src_box['x'] + src_box['width']/2, src_box['y'] + src_box['height']/2)
            page.mouse.down()
            page.mouse.move(tgt_box['x'] + tgt_box['width']/2, tgt_box['y'] + tgt_box['height']/2, steps=15)
            page.mouse.up()
            time.sleep(0.5)
            print("Connection attempt completed")
        else:
            print("Could not get handle positions")
    elif len(nodes) == 1:
        print("Only 1 node found - cannot test node-to-node connection")
    else:
        print("No nodes found on canvas")
    
    # Final screenshot
    page.screenshot(path='screenshot_final.png', full_page=True)
    print("\n[Screenshot] screenshot_final.png saved")
    
    browser.close()
    print("\n=== VERIFICATION COMPLETE ===")

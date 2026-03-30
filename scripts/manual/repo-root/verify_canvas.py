from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    # Navigate to the app
    print("=== NAVIGATING TO LOCAL APP ===")
    page.goto('http://localhost:15191')
    page.wait_for_load_state('networkidle')
    
    # Take initial screenshot
    print("=== TAKING INITIAL CANVAS SCREENSHOT ===")
    page.screenshot(path='01_initial_canvas.png', full_page=True)
    
    # Check for page title
    print(f"=== PAGE TITLE: {page.title()} ===")
    
    # Check for top-left menu
    print("\n=== CHECKING TOP-LEFT FILE/EDIT MENU ===")
    menu_items = page.locator('[role="menubar"] button, .menu button, [class*="menu"] button, header button, nav button').all()
    print(f"Found {len(menu_items)} potential menu buttons")
    for i, item in enumerate(menu_items[:6]):
        text = item.inner_text().strip() if item.is_visible() else "N/A"
        print(f"  Menu item {i+1}: '{text}' (visible: {item.is_visible()})")
    
    # Try specific selectors for File/Edit
    file_edit_items = page.locator('text=File, text=Edit').all()
    print(f"File/Edit found: {len(file_edit_items)}")
    
    # Check for any menu bar or top navigation
    top_nav = page.locator('header, [class*="header"], [class*="menu-bar"], [class*="menubar"]').first
    if top_nav.is_visible():
        print(f"Top nav visible: {top_nav.inner_text()[:200]}")
    
    # Screenshot after checking menu
    page.screenshot(path='02_menu_check.png', full_page=True)
    
    # Look for profile/personal center button
    print("\n=== LOOKING FOR PROFILE PANEL ===")
    profile_selectors = [
        '[class*="profile"]',
        '[class*="user"]',
        '[class*="avatar"]',
        '[class*="personal"]',
        'button:has-text("Profile")',
        'button:has-text("User")',
        '[data-testid*="profile"]',
        '[data-testid*="user"]'
    ]
    profile_found = False
    for selector in profile_selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible():
                print(f"Found profile element with selector: {selector}")
                profile_found = True
                el.click()
                time.sleep(0.5)
                break
        except:
            continue
    
    if profile_found:
        print("Profile panel opened")
        page.screenshot(path='03_profile_panel.png', full_page=True)
        
        # Check for tabs
        print("\n=== CHECKING FOR TABS (overview/recharge/ledger/settings) ===")
        tab_keywords = ['overview', 'recharge', 'ledger', 'settings']
        for keyword in tab_keywords:
            tab = page.locator(f'text={keyword}').first
            if tab.is_visible():
                print(f"  Tab '{keyword}' found and visible")
    else:
        print("Profile panel not found with standard selectors")
    
    # Look for nodes to test connection
    print("\n=== CHECKING FOR NODES ===")
    nodes = page.locator('[class*="node"], [data-id], .react-flow__node').all()
    print(f"Found {len(nodes)} potential nodes")
    
    if len(nodes) >= 2:
        print(f"Attempting connection between nodes...")
        # Take screenshot of nodes
        page.screenshot(path='04_nodes_found.png', full_page=True)
        
        # Look for handles
        handles = page.locator('[class*="handle"], .react-flow__handle').all()
        print(f"Found {len(handles)} handles")
        
        if len(handles) >= 2:
            # Try to drag from first handle to second
            try:
                source = handles[0]
                target = handles[1]
                source_box = source.bounding_box()
                target_box = target.bounding_box()
                print(f"Source handle at: {source_box}")
                print(f"Target handle at: {target_box}")
                
                # Drag from source to target
                page.mouse.move(source_box['x'] + source_box['width']/2, source_box['y'] + source_box['height']/2)
                page.mouse.down()
                page.mouse.move(target_box['x'] + target_box['width']/2, target_box['y'] + target_box['height']/2, steps=10)
                page.mouse.up()
                time.sleep(0.5)
                
                page.screenshot(path='05_after_connection_attempt.png', full_page=True)
                print("Connection attempt completed")
            except Exception as e:
                print(f"Connection attempt failed: {e}")
    
    browser.close()
    print("\n=== VERIFICATION COMPLETE ===")

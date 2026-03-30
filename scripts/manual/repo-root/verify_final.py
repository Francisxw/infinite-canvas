from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    print("Loading app...")
    page.goto('http://localhost:15191')
    page.wait_for_load_state('networkidle')
    time.sleep(1)
    
    # Save initial screenshot
    page.screenshot(path='screenshot_01_initial.png', full_page=True)
    print("[1] Screenshot saved: screenshot_01_initial.png")
    
    # Check title
    print(f"\nPage Title: {page.title()}")
    
    # Check top-left menu using JavaScript to avoid encoding issues
    print("\n=== TOP-LEFT MENU CHECK ===")
    menu_info = page.evaluate('''() => {
        const menuBtns = Array.from(document.querySelectorAll('button')).filter(b => {
            const rect = b.getBoundingClientRect();
            return rect.top < 80 && rect.left < 200;
        });
        return menuBtns.map(b => ({
            text: b.textContent.trim(),
            visible: b.offsetParent !== null,
            clickable: !b.disabled
        }));
    }''')
    
    print(f"Found {len(menu_info)} menu buttons in top-left:")
    for i, btn in enumerate(menu_info):
        status = "OK" if btn['visible'] else "HIDDEN"
        print(f"  [{i}] Text: '{btn['text']}' - {status}, clickable: {btn['clickable']}")
    
    # Click first menu button to test interactivity
    if len(menu_info) >= 2:
        first_btn = page.locator('button').nth(0)
        if first_btn.is_visible():
            print("\nTesting menu interactivity...")
            first_btn.click()
            time.sleep(0.3)
            page.screenshot(path='screenshot_02_menu_clicked.png')
            print("[2] Screenshot saved: screenshot_02_menu_clicked.png")
    
    # Look for profile/personal center
    print("\n=== PROFILE PANEL CHECK ===")
    
    # Look for user-related elements
    profile_elements = page.evaluate('''() => {
        const all = Array.from(document.querySelectorAll('*'));
        const candidates = all.filter(el => {
            const text = el.textContent?.toLowerCase() || '';
            const cls = el.className?.toLowerCase() || '';
            return (text.includes('user') || text.includes('profile') || text.includes('personal') || 
                    cls.includes('user') || cls.includes('profile') || cls.includes('avatar'))
                    && el.children.length < 3;
        }).slice(0, 10);
        return candidates.map(el => ({
            tag: el.tagName,
            text: el.textContent.trim().slice(0, 50),
            class: el.className.slice(0, 50)
        }));
    }''')
    
    print(f"Found {len(profile_elements)} profile-related elements:")
    for el in profile_elements:
        print(f"  - {el['tag']}: '{el['text']}' (class: {el['class']})")
    
    # Look for icon buttons or avatar in top-right
    top_right = page.evaluate('''() => {
        const all = Array.from(document.querySelectorAll('button, [role="button"], .avatar, [class*="avatar"], [class*="user"]'));
        return all.filter(el => {
            const rect = el.getBoundingClientRect();
            return rect.top < 80 && rect.right > window.innerWidth - 200;
        }).map(el => ({
            tag: el.tagName,
            text: el.textContent.trim().slice(0, 30),
            class: el.className.slice(0, 40),
            rect: {right: el.getBoundingClientRect().right, top: el.getBoundingClientRect().top}
        }));
    }''')
    
    print(f"\nTop-right elements (possible profile triggers): {len(top_right)}")
    for el in top_right:
        print(f"  - {el['tag']}: '{el['text']}' (class: {el['class']})")
    
    # Try clicking any avatar/user button
    if len(top_right) > 0:
        for i in range(min(5, len(top_right))):
            try:
                btn = page.locator('button').nth(-1-i)  # Try last buttons
                if btn.is_visible():
                    print(f"\nClicking button at position...")
                    btn.click()
                    time.sleep(0.5)
                    page.screenshot(path='screenshot_03_profile_opened.png')
                    print("[3] Screenshot saved: screenshot_03_profile_opened.png")
                    
                    # Check for tabs
                    tabs_check = page.evaluate('''() => {
                        const tabKeywords = ['overview', 'recharge', 'ledger', 'settings'];
                        const found = [];
                        tabKeywords.forEach(kw => {
                            const el = Array.from(document.querySelectorAll('*')).find(e => 
                                e.textContent.toLowerCase().includes(kw) && e.children.length < 2
                            );
                            if (el) found.push({keyword: kw, text: el.textContent.trim().slice(0, 30)});
                        });
                        return found;
                    }''')
                    
                    if tabs_check:
                        print(f"\nTabs found after clicking:")
                        for t in tabs_check:
                            print(f"  - {t['keyword']}: '{t['text']}'")
                    break
            except Exception as e:
                continue
    
    # Check nodes and handles
    print("\n=== NODES & CONNECTIONS CHECK ===")
    nodes = page.locator('.react-flow__node').all()
    handles = page.locator('.react-flow__handle').all()
    print(f"React Flow nodes: {len(nodes)}")
    print(f"Connection handles: {len(handles)}")
    
    if len(nodes) >= 2 and len(handles) >= 2:
        print("\nAttempting node-to-node connection...")
        page.screenshot(path='screenshot_04_before_connection.png')
        
        try:
            source = handles[0]
            target = handles[1]
            src_box = source.bounding_box()
            tgt_box = target.bounding_box()
            
            print(f"Source handle: ({src_box['x']:.0f}, {src_box['y']:.0f})")
            print(f"Target handle: ({tgt_box['x']:.0f}, {tgt_box['y']:.0f})")
            
            # Perform drag
            page.mouse.move(src_box['x'] + src_box['width']/2, src_box['y'] + src_box['height']/2)
            page.mouse.down()
            page.mouse.move(tgt_box['x'] + tgt_box['width']/2, tgt_box['y'] + tgt_box['height']/2, steps=15)
            page.mouse.up()
            time.sleep(0.5)
            
            page.screenshot(path='screenshot_05_after_connection.png')
            print("[5] Screenshot saved: screenshot_05_after_connection.png")
            print("Connection attempt completed")
        except Exception as e:
            print(f"Connection attempt failed: {e}")
    elif len(nodes) == 1:
        print("\nOnly 1 node found - cannot test node-to-node connection")
        page.screenshot(path='screenshot_04_single_node.png')
    else:
        print("\nNo nodes found on canvas")
    
    browser.close()
    print("\n=== VERIFICATION COMPLETE ===")

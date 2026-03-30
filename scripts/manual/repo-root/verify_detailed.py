from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    print("=== NAVIGATING TO APP ===")
    page.goto('http://localhost:15191')
    page.wait_for_load_state('networkidle')
    
    # Get page info
    title = page.title()
    print(f"\n[OK] PAGE TITLE: {title}")
    
    # Get all buttons and their text
    print("\n=== ALL BUTTONS ON PAGE ===")
    buttons = page.locator('button').all()
    for i, btn in enumerate(buttons):
        if btn.is_visible():
            text = btn.inner_text().strip()[:50]
            print(f"  [{i}] '{text}'")
    
    # Get all visible text from header/top area
    print("\n=== HEADER/TOP AREA TEXT ===")
    header_area = page.locator('header, .header, [class*="header"]').first
    if header_area.is_visible():
        print(f"  Header text: {header_area.inner_text()[:300]}")
    
    # Check top-left corner specifically
    print("\n=== TOP-LEFT AREA (File/Edit Menu Check) ===")
    # Get elements in top-left
    top_left = page.evaluate('''() => {
        const elements = document.querySelectorAll('*');
        const topLeftElements = [];
        for (const el of elements) {
            const rect = el.getBoundingClientRect();
            if (rect.top < 100 && rect.left < 300 && rect.width > 20 && rect.height > 20 && el.children.length < 5) {
                const text = el.innerText?.trim();
                if (text && text.length < 50) {
                    topLeftElements.push({
                        tag: el.tagName,
                        text: text,
                        class: el.className,
                        rect: {top: rect.top, left: rect.left, width: rect.width, height: rect.height}
                    });
                }
            }
        }
        return topLeftElements.slice(0, 15);
    }''')
    print(f"  Top-left elements found: {len(top_left)}")
    for el in top_left:
        cls = el['class'][:40] if el['class'] else 'none'
        print(f"    - {el['tag']}: '{el['text']}' (class: {cls})")
    
    # Look for profile panel with specific tab text
    print("\n=== PROFILE PANEL & TABS CHECK ===")
    tab_names = ['Overview', 'overview', 'Recharge', 'recharge', 'Ledger', 'ledger', 'Settings', 'settings']
    found_tabs = []
    for tab in tab_names:
        locator = page.locator(f'text="{tab}"').first
        try:
            if locator.is_visible():
                found_tabs.append(tab)
        except:
            pass
    print(f"  Found tab texts: {found_tabs if found_tabs else 'None visible'}")
    
    # Try to find and click profile/user button
    user_btn = page.locator('button:has-text("User"), button:has-text("Profile"), [class*="user"], [class*="profile"]').first
    if user_btn.is_visible():
        print(f"  Found user/profile button: '{user_btn.inner_text().strip()[:50]}'")
        user_btn.click()
        page.wait_for_timeout(500)
        
        # Check again for tabs after clicking
        print("\n  After clicking profile, checking for tabs:")
        for tab in tab_names:
            locator = page.locator(f'text="{tab}"').first
            try:
                if locator.is_visible():
                    print(f"    [OK] Tab '{tab}' is visible")
            except:
                pass
    
    # Check for nodes and handles
    print("\n=== NODES & CONNECTIONS CHECK ===")
    nodes = page.locator('.react-flow__node').all()
    print(f"  React Flow nodes found: {len(nodes)}")
    
    handles = page.locator('.react-flow__handle').all()
    print(f"  Connection handles found: {len(handles)}")
    
    if len(nodes) > 0:
        print(f"  First node text: {nodes[0].inner_text()[:100]}")
    
    # Get page HTML structure for debugging
    print("\n=== PAGE STRUCTURE (first 2000 chars) ===")
    body_html = page.locator('body').inner_html()[:2000]
    print(body_html.replace('\n', ' ')[:2000])
    
    browser.close()

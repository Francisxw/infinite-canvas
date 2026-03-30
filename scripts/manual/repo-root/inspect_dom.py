from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    print("Loading app...")
    page.goto('http://localhost:15191')
    page.wait_for_load_state('networkidle')
    time.sleep(1)
    
    # Get initial HTML structure
    print("\n=== PAGE STRUCTURE ===")
    structure = page.evaluate('''() => {
        const getStructure = (el, depth = 0) => {
            if (depth > 3) return null;
            const children = Array.from(el.children).map(c => getStructure(c, depth + 1)).filter(Boolean);
            return {
                tag: el.tagName,
                id: el.id,
                classes: el.className,
                childCount: el.children.length,
                text: el.textContent.slice(0, 100),
                children: children.slice(0, 5)
            };
        };
        return getStructure(document.body);
    }''')
    
    def print_struct(s, indent=0):
        prefix = "  " * indent
        cls = s.get('classes', '')[:40]
        print(f"{prefix}{s['tag']}{' #' + s['id'] if s['id'] else ''}{' .' + cls if cls else ''}")
        if s.get('children'):
            for c in s['children']:
                print_struct(c, indent + 1)
    
    print_struct(structure)
    
    # Get all button texts
    print("\n=== ALL BUTTONS ===")
    buttons = page.evaluate('''() => {
        return Array.from(document.querySelectorAll('button')).map((b, i) => ({
            index: i,
            text: b.textContent.trim(),
            class: b.className,
            disabled: b.disabled,
            rect: b.getBoundingClientRect()
        }));
    }''')
    
    for b in buttons:
        r = b['rect']
        print(f"  [{b['index']}] '{b['text']}' - class: {b['class'][:30] if b['class'] else 'none'} - pos: ({r['x']:.0f}, {r['y']:.0f})")
    
    # Try to click first two buttons (File/Edit)
    if len(buttons) >= 2:
        print("\n=== TESTING MENU INTERACTIVITY ===")
        first_btn = page.locator('button').nth(0)
        print(f"Clicking button 0...")
        first_btn.click()
        time.sleep(0.3)
        
        # Check if anything changed (dropdown appeared)
        page.screenshot(path='screenshot_after_first_click.png')
        print("Screenshot saved: screenshot_after_first_click.png")
    
    # Look for user/avatar/profile area
    print("\n=== LOOKING FOR PROFILE AREA ===")
    
    # Try clicking buttons from the end (usually profile is on the right)
    btn_count = len(buttons)
    if btn_count > 0:
        print(f"Trying buttons from index {btn_count-1} backwards...")
        for i in range(min(3, btn_count)):
            idx = btn_count - 1 - i
            try:
                btn = page.locator('button').nth(idx)
                if btn.is_visible():
                    print(f"Clicking button {idx}...")
                    btn.click()
                    time.sleep(0.5)
                    
                    # Check for tabs
                    content = page.evaluate('''() => document.body.innerText''')
                    print(f"\n  Checking for tabs in page text after click {idx}:")
                    for tab in ['Overview', 'Recharge', 'Ledger', 'Settings']:
                        if tab in content:
                            print(f"    [FOUND] {tab}")
                    
                    page.screenshot(path=f'screenshot_after_click_{idx}.png')
                    print(f"  Screenshot saved: screenshot_after_click_{idx}.png")
            except Exception as e:
                print(f"  Error clicking button {idx}: {e}")
    
    # Check for React Flow
    print("\n=== REACT FLOW CHECK ===")
    rf_check = page.evaluate('''() => ({
        nodes: document.querySelectorAll('.react-flow__node').length,
        handles: document.querySelectorAll('.react-flow__handle').length,
        edges: document.querySelectorAll('.react-flow__edge').length
    })''')
    print(f"  Nodes: {rf_check['nodes']}")
    print(f"  Handles: {rf_check['handles']}")
    print(f"  Edges: {rf_check['edges']}")
    
    browser.close()
    print("\n=== DONE ===")

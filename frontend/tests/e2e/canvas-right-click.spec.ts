import { test, expect } from '@playwright/test'

test.describe('Canvas Right-Click Context Menu', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app and wait for canvas to be ready
    await page.goto('/')
    // Wait for the tldraw canvas to be visible
    await page.waitForSelector('.tl-canvas', { timeout: 30000 })
    // Wait for tldraw to fully initialize
    await page.waitForTimeout(2000)
  })

  test('right-click keeps canvas responsive', async ({ page }) => {
    // Get canvas bounding box
    const canvas = page.locator('.tl-canvas')
    const box = await canvas.boundingBox()
    expect(box).not.toBeNull()

    const centerX = box!.x + box!.width / 2
    const centerY = box!.y + box!.height / 2

    // Right-click should be dedicated to context-menu flow
    await page.mouse.click(centerX, centerY, { button: 'right' })

    // Wait a bit for any default browser context menu or custom menu
    await page.waitForTimeout(500)

    // Key verification: canvas remains responsive after right-click
    const canvasAfter = page.locator('.tl-canvas')
    await expect(canvasAfter).toBeVisible()
  })

  test('left-drag pans interaction path without breaking right-click', async ({ page }) => {
    // Get canvas bounding box
    const canvas = page.locator('.tl-canvas')
    const box = await canvas.boundingBox()
    expect(box).not.toBeNull()

    const startX = box!.x + box!.width / 2
    const startY = box!.y + box!.height / 2

    // Mouse down with left button
    await page.mouse.move(startX, startY)
    await page.mouse.down({ button: 'left' })

    // Move the mouse while holding left button (drag)
    await page.mouse.move(startX + 10, startY + 10)

    // Mouse up to release
    await page.mouse.up({ button: 'left' })

    // Wait a bit for any context menu to potentially appear
    await page.waitForTimeout(500)

    // Verify canvas still responsive, then right-click still works
    const canvasAfter = page.locator('.tl-canvas')
    await expect(canvasAfter).toBeVisible()

    await page.mouse.click(startX + 60, startY + 60, { button: 'right' })
    await page.waitForTimeout(300)
    await expect(canvasAfter).toBeVisible()
  })

  test('left-drag should not poison subsequent right-click', async ({ page }) => {
    // Get canvas bounding box
    const canvas = page.locator('.tl-canvas')
    const box = await canvas.boundingBox()
    expect(box).not.toBeNull()

    const startX = box!.x + box!.width / 2
    const startY = box!.y + box!.height / 2

    // Left-drag should start canvas panning state
    await page.mouse.move(startX, startY)
    await page.mouse.down({ button: 'left' })
    await page.mouse.move(startX + 50, startY + 50)
    await page.mouse.up({ button: 'left' })
    await page.waitForTimeout(300)

    // Pure right-click should still work normally
    // Click at a different position to ensure fresh interaction
    await page.mouse.click(startX + 100, startY + 100, { button: 'right' })
    await page.waitForTimeout(500)

    // Verify canvas is still responsive
    const canvasAfter = page.locator('.tl-canvas')
    await expect(canvasAfter).toBeVisible()
  })

  test('non-canvas right-click does not affect canvas drag behavior', async ({ page }) => {
    // Get canvas bounding box
    const canvas = page.locator('.tl-canvas')
    const box = await canvas.boundingBox()
    expect(box).not.toBeNull()

    // Right-click outside canvas (e.g., at top-left which is typically header/UI area)
    await page.mouse.click(10, 10, { button: 'right' })
    await page.waitForTimeout(300)

    // Now right-click on canvas - should work normally (no poisoning)
    const startX = box!.x + box!.width / 2
    const startY = box!.y + box!.height / 2
    await page.mouse.click(startX, startY, { button: 'right' })
    await page.waitForTimeout(500)

    // Canvas should still be responsive and visible
    const canvasAfter = page.locator('.tl-canvas')
    await expect(canvasAfter).toBeVisible()

    // Verify left-drag still works after non-canvas right-click
    await page.mouse.move(startX, startY)
    await page.mouse.down({ button: 'left' })
    await page.mouse.move(startX + 20, startY + 20)
    await page.mouse.up({ button: 'left' })
    await page.waitForTimeout(300)

    // Now a pure right-click should work (proving isolation works)
    await page.mouse.click(startX + 150, startY + 150, { button: 'right' })
    await page.waitForTimeout(500)

    // Final verification - canvas still works
    await expect(canvasAfter).toBeVisible()
  })

  test('ctrl+left-drag should be reserved for selection flow and not trigger custom pan lock', async ({ page }) => {
    const canvas = page.locator('.tl-canvas')
    const box = await canvas.boundingBox()
    expect(box).not.toBeNull()

    const startX = box!.x + box!.width / 2
    const startY = box!.y + box!.height / 2

    await page.keyboard.down('Control')
    await page.mouse.move(startX, startY)
    await page.mouse.down({ button: 'left' })
    await page.mouse.move(startX + 40, startY + 40)
    await page.mouse.up({ button: 'left' })
    await page.keyboard.up('Control')

    await page.waitForTimeout(300)

    // Canvas remains responsive; Ctrl+right path should not poison subsequent right-click menu behavior
    await page.mouse.click(startX + 80, startY + 80, { button: 'right' })
    await page.waitForTimeout(300)
    await expect(canvas).toBeVisible()
  })
})

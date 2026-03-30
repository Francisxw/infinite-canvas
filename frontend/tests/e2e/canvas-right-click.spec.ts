import { expect, test } from '@playwright/test'

test.describe('Canvas context menu', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate(() => {
      window.localStorage.removeItem('infinite-canvas-flow')
      window.localStorage.removeItem('infinite-canvas-project')
    })
    await page.reload()
    await page.waitForSelector('.react-flow', { timeout: 30000 })
    await page.waitForSelector('.react-flow__pane', { timeout: 30000 })
    await page.waitForTimeout(300)
  })

  test('right-click opens create menu and left-click pane closes it', async ({ page }) => {
    const pane = page.locator('.react-flow__pane')
    const contextMenu = page.getByTestId('canvas-context-menu')
    const box = await pane.boundingBox()
    expect(box).not.toBeNull()

    const x = box!.x + box!.width / 2
    const y = box!.y + box!.height / 2

    await page.mouse.click(x, y, { button: 'right' })
    await expect(contextMenu).toBeVisible()
    await expect(contextMenu.getByRole('button', { name: '文本 创建文本卡片' })).toBeVisible()
    await expect(contextMenu.getByRole('button', { name: '图片' })).toBeVisible()
    await expect(contextMenu.getByRole('button', { name: '视频' })).toBeVisible()

    await page.mouse.click(x + 60, y + 60, { button: 'left' })
    await expect(contextMenu).toHaveCount(0)
  })

  test('right-click menu can create a video node', async ({ page }) => {
    const pane = page.locator('.react-flow__pane')
    const box = await pane.boundingBox()
    expect(box).not.toBeNull()

    // Click in bottom-right area, away from initial nodes (image at 320,220; text at 860,240; video at 320,500)
    const x = box!.x + box!.width * 0.8
    const y = box!.y + box!.height * 0.8

    await page.mouse.click(x, y, { button: 'right' })

    // Verify menu is visible before attempting to click
    const contextMenu = page.getByTestId('canvas-context-menu')
    await expect(contextMenu).toBeVisible()

    const initialVideoNodes = await page.locator('[data-testid^="rf__node-video-node"]').count()
    await contextMenu.getByRole('button', { name: '视频' }).click()
    await expect(page.locator('[data-testid^="rf__node-video-node"]')).toHaveCount(initialVideoNodes + 1)
  })
})

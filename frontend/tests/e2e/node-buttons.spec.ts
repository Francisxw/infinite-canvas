import { expect, test } from '@playwright/test'

async function resetCanvas(page: import('@playwright/test').Page) {
  await page.goto('/')
  await page.evaluate(() => {
    window.localStorage.removeItem('infinite-canvas-flow')
    window.localStorage.removeItem('infinite-canvas-project')
  })
  await page.reload()
  await page.waitForSelector('.react-flow', { timeout: 30000 })
  await page.waitForTimeout(300)
}

async function createNode(page: import('@playwright/test').Page, type: 'text' | 'image') {
  await page.getByRole('button', { name: '新建节点' }).click()
  await expect(page.getByTestId('dock-create-panel')).toBeVisible()

  if (type === 'text') {
    await page.getByTestId('dock-create-text').click()
    return
  }

  await page.getByTestId('dock-create-image').click()
}

test.describe('Node ports and controls', () => {
  test.beforeEach(async ({ page }) => {
    await resetCanvas(page)
    await createNode(page, 'text')
    await createNode(page, 'image')
  })

  test('port handles are visible; payload panels stay open for multi-select and support click pin', async ({ page }) => {
    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    const imageNode = page.locator('[data-testid^="rf__node-image-node"]').first()

    await textNode.click()
    await textNode.locator('[data-testid="text-preview-frame"]').dblclick()
    await textNode.getByLabel('text node editor').fill('hover payload smoke')
    await textNode.getByLabel('text node editor').blur()

    const textOutput = textNode.getByLabel('text-node-output-port')
    const imageInput = imageNode.getByLabel('image-node-input-port')

    await expect(textOutput).toBeVisible()
    await expect(imageInput).toBeVisible()

    await textNode.locator('[data-testid="text-preview-frame"]').hover()
    await expect(textNode.getByText('输出数据')).toBeHidden()

    await textOutput.hover()
    await expect(textNode.getByText('输出数据')).toBeVisible()
    await expect(textNode.getByRole('button', { name: /hover payload smok/ })).toBeVisible()

    await textOutput.click()
    await textNode.locator('[data-testid="text-preview-frame"]').hover()
    await expect(textNode.getByText('输出数据')).toBeVisible()
    await textNode.getByRole('button', { name: /hover payload smok/ }).click()
    await expect(textNode.getByText('输出数据')).toBeVisible()
    await expect(textNode.getByRole('button', { name: /hover payload smok/ })).toBeVisible()

    await imageInput.hover()
    await expect(imageNode.getByText('输入数据')).toBeVisible()
  })

  test('text node supports direct editing and has resize controls removed', async ({ page }) => {
    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    await textNode.click()

    const frame = textNode.locator('[data-testid="text-preview-frame"]')
    await frame.dblclick()

    const editor = textNode.getByLabel('text node editor')
    await editor.fill('manual edit works')
    await editor.blur()
    await expect(textNode.getByTestId('text-node-display')).toContainText('manual edit works')

    await expect(textNode.locator('.react-flow__resize-control')).toHaveCount(0)
  })

  test('text node list mode renders actual bullet list in display', async ({ page }) => {
    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    await textNode.click()

    // Enable list mode via settings (click the format button showing "Large", "Medium", or "Compact")
    await textNode.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /Large|Medium|Compact/ }).click()
    await textNode.getByRole('button', { name: 'List' }).click()

    // Close settings panel by pressing Escape
    await page.keyboard.press('Escape')

    // Enter multiline text
    const frame = textNode.locator('[data-testid="text-preview-frame"]')
    await frame.dblclick()
    const editor = textNode.getByLabel('text node editor')
    await editor.fill('First item\nSecond item\nThird item')
    await editor.blur()

    // Verify actual <ul> with <li> elements is rendered
    const listDisplay = textNode.locator('ul[data-testid="text-node-display"]')
    await expect(listDisplay).toBeVisible()
    await expect(listDisplay.locator('li')).toHaveCount(3)
    await expect(listDisplay.locator('li').nth(0)).toHaveText('First item')
    await expect(listDisplay.locator('li').nth(1)).toHaveText('Second item')
    await expect(listDisplay.locator('li').nth(2)).toHaveText('Third item')

    // Disable list mode and verify plain text display returns
    await textNode.locator('button').filter({ has: page.locator('svg') }).filter({ hasText: /Large|Medium|Compact/ }).click()
    await textNode.getByRole('button', { name: 'List' }).click()
    await page.keyboard.press('Escape')
    const plainDisplay = textNode.locator('div[data-testid="text-node-display"]')
    await expect(plainDisplay).toBeVisible()
    await expect(plainDisplay).toContainText('First item')
  })
})

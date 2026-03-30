import { expect, test } from '@playwright/test'

test.describe('Persistence migration', () => {
  test('legacy tldraw edge migrates to custom and remains deletable', async ({ page }) => {
    const legacyProject = {
      records: [
        {
          id: 'shape:text-legacy',
          typeName: 'shape',
          type: 'text-node',
          x: 120,
          y: 120,
          props: { w: 320, h: 240, text: 'legacy text', heading: 1, bold: false, italic: false, list: false },
        },
        {
          id: 'shape:image-legacy',
          typeName: 'shape',
          type: 'image-node',
          x: 620,
          y: 120,
          props: { w: 390, h: 292, prompt: 'legacy image', model: 'google/gemini-3.1-flash-image-preview', aspectRatio: '1:1', imageSize: '1K', numImages: 1 },
        },
        {
          id: 'shape:arrow-legacy',
          typeName: 'shape',
          type: 'arrow',
        },
        {
          id: 'binding:arrow-start',
          typeName: 'binding',
          type: 'arrow',
          fromId: 'shape:arrow-legacy',
          toId: 'shape:text-legacy',
          props: { terminal: 'start' },
        },
        {
          id: 'binding:arrow-end',
          typeName: 'binding',
          type: 'arrow',
          fromId: 'shape:arrow-legacy',
          toId: 'shape:image-legacy',
          props: { terminal: 'end' },
        },
      ],
    }

    await page.addInitScript((project) => {
      window.localStorage.removeItem('infinite-canvas-flow')
      window.localStorage.setItem('infinite-canvas-project', JSON.stringify(project))
    }, legacyProject)

    await page.goto('/')
    await page.waitForSelector('.react-flow', { timeout: 30000 })

    await expect(page.locator('.react-flow__edge')).toHaveCount(1)
    await expect(page.getByRole('button', { name: 'delete edge' })).toBeVisible()

    await page.getByRole('button', { name: 'delete edge' }).click({ force: true })
    await expect(page.locator('.react-flow__edge')).toHaveCount(0)
  })
})

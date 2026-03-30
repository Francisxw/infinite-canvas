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

async function createNode(page: import('@playwright/test').Page, type: 'text' | 'image' | 'video') {
  await page.getByRole('button', { name: '新建节点' }).click()
  await expect(page.getByTestId('dock-create-panel')).toBeVisible()

  if (type === 'text') {
    await page.getByTestId('dock-create-text').click()
    return
  }

  if (type === 'image') {
    await page.getByTestId('dock-create-image').click()
    return
  }

  await page.getByTestId('dock-create-video').click()
}

async function createNodeAt(page: import('@playwright/test').Page, type: 'text' | 'image' | 'video', xRatio: number, yRatio: number) {
  const flow = page.locator('.react-flow')
  const flowBox = await flow.boundingBox()
  expect(flowBox).not.toBeNull()

  const clickX = flowBox!.x + flowBox!.width * xRatio
  const clickY = flowBox!.y + flowBox!.height * yRatio

  await page.mouse.dblclick(clickX, clickY)
  await expect(page.getByTestId('canvas-context-menu')).toBeVisible()

  if (type === 'text') {
    await page.getByRole('button', { name: /文本/ }).click()
  } else if (type === 'image') {
    await page.getByRole('button', { name: '图片' }).click()
  } else {
    await page.getByRole('button', { name: '视频' }).click()
  }

  await page.waitForTimeout(250)
}

test.describe('Flow nodes interactions', () => {
  test.beforeEach(async ({ page }) => {
    await resetCanvas(page)
  })

  test('dock creates a new text node and persistence works', async ({ page }) => {
    await createNode(page, 'text')

    await expect(page.locator('[data-testid^="rf__node-text-node"]')).toHaveCount(1)

    await page.reload()
    await page.waitForSelector('.react-flow', { timeout: 30000 })
    await expect(page.locator('[data-testid^="rf__node-text-node"]')).toHaveCount(1)
  })

  test('dock creates a node near viewport center after pan and zoom', async ({ page }) => {
    const flow = page.locator('.react-flow')
    const flowBox = await flow.boundingBox()
    expect(flowBox).not.toBeNull()

    const centerX = flowBox!.x + flowBox!.width / 2
    const centerY = flowBox!.y + flowBox!.height / 2

    await page.mouse.move(centerX, centerY)
    await page.mouse.down()
    await page.mouse.move(centerX + 180, centerY + 120, { steps: 12 })
    await page.mouse.up()
    await flow.hover()
    await page.mouse.wheel(0, -900)
    await page.waitForTimeout(200)

    await createNode(page, 'text')

    const newNode = page.locator('[data-testid^="rf__node-text-node"]').last()
    const nodeBox = await newNode.boundingBox()
    expect(nodeBox).not.toBeNull()

    const nodeCenterX = nodeBox!.x + nodeBox!.width / 2
    const nodeCenterY = nodeBox!.y + nodeBox!.height / 2
    expect(Math.abs(nodeCenterX - centerX)).toBeLessThan(180)
    expect(Math.abs(nodeCenterY - centerY)).toBeLessThan(180)
  })

  test('text output connects to video node and propagates prompt data', async ({ page }) => {
    test.setTimeout(60000)
    await createNodeAt(page, 'text', 0.32, 0.42)
    await createNodeAt(page, 'video', 0.7, 0.42)

    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    const videoNode = page.locator('[data-testid^="rf__node-video-node"]').first()

    await textNode.locator('[data-testid="text-preview-frame"]').dblclick({ force: true })
    const editor = textNode.getByLabel('text node editor')
    await editor.fill('sunlit editorial portrait')
    await editor.blur()

    const sourcePort = textNode.getByLabel('text-node-output-port')
    const targetFrame = await videoNode.locator('[data-preview-frame="video"]').boundingBox()
    const sourceBox = await sourcePort.boundingBox()
    expect(sourceBox).not.toBeNull()
    expect(targetFrame).not.toBeNull()

    await page.mouse.move(sourceBox!.x + sourceBox!.width / 2, sourceBox!.y + sourceBox!.height / 2)
    await page.mouse.down()
    await page.mouse.move(targetFrame!.x + 24, targetFrame!.y + targetFrame!.height / 2, { steps: 16 })
    await page.mouse.up()

    await expect(page.locator('.react-flow__edge')).toHaveCount(1, { timeout: 10000 })

    await videoNode.click({ force: true })
    const videoPrompt = videoNode.getByPlaceholder('描述任何你想要生成的视频内容')
    await expect(videoPrompt).toHaveValue('sunlit editorial portrait')
  })

  test('near-miss release still connects through fallback target selection', async ({ page }) => {
    test.setTimeout(60000)
    await createNodeAt(page, 'text', 0.32, 0.42)
    await createNodeAt(page, 'video', 0.7, 0.42)

    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    const videoNode = page.locator('[data-testid^="rf__node-video-node"]').first()

    await textNode.locator('[data-testid="text-preview-frame"]').dblclick({ force: true })
    const editor = textNode.getByLabel('text node editor')
    await editor.fill('fallback connection prompt')
    await editor.blur()

    const sourcePort = textNode.getByLabel('text-node-output-port')
    const sourceBox = await sourcePort.boundingBox()
    const targetFrame = await videoNode.locator('[data-preview-frame="video"]').boundingBox()
    expect(sourceBox).not.toBeNull()
    expect(targetFrame).not.toBeNull()

    await page.mouse.move(sourceBox!.x + sourceBox!.width / 2, sourceBox!.y + sourceBox!.height / 2)
    await page.mouse.down()
    await page.mouse.move(targetFrame!.x + 12, targetFrame!.y + targetFrame!.height / 2, { steps: 16 })
    await page.mouse.move(targetFrame!.x - 10, targetFrame!.y + targetFrame!.height / 2, { steps: 4 })
    await page.mouse.up()

    await expect(page.locator('.react-flow__edge')).toHaveCount(1, { timeout: 10000 })

    await videoNode.click({ force: true })
    const videoPrompt = videoNode.getByPlaceholder('描述任何你想要生成的视频内容')
    await expect(videoPrompt).toHaveValue('fallback connection prompt')
  })

  test('video upload shows playable preview', async ({ page }) => {
    await page.route('**/api/upload', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          filename: 'flower.mp4',
          content_type: 'video/mp4',
          size: 1024,
          data_url: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4',
        }),
      })
    })

    await createNode(page, 'video')
    const videoNode = page.locator('[data-testid^="rf__node-video-node"]').first()
    await videoNode.click()
    const uploadButton = videoNode.getByRole('button', { name: '上传' })
    await expect(uploadButton).toBeVisible()

    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      uploadButton.click(),
    ])

    await chooser.setFiles({
      name: 'sample.mp4',
      mimeType: 'video/mp4',
      buffer: Buffer.from('fake-video-payload'),
    })

    const preview = videoNode.locator('video').first()
    await expect(preview).toBeVisible()
    await expect(preview).toHaveAttribute('src', /flower\.mp4/)
  })

  test('clicking a handle without drag does not create a new edge', async ({ page }) => {
    await createNode(page, 'text')
    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    await expect(page.locator('.react-flow__edge')).toHaveCount(0)

    await textNode.getByLabel('text-node-output-port').click()
    await page.waitForTimeout(200)

    await expect(page.locator('.react-flow__edge')).toHaveCount(0)
  })

  test('self-connection is blocked for a single node', async ({ page }) => {
    await createNode(page, 'text')
    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    await expect(page.locator('.react-flow__edge')).toHaveCount(0)

    const sourcePort = textNode.getByLabel('text-node-output-port')
    const targetPort = textNode.getByLabel('text-node-input-port')
    const sourceBox = await sourcePort.boundingBox()
    const targetBox = await targetPort.boundingBox()
    expect(sourceBox).not.toBeNull()
    expect(targetBox).not.toBeNull()

    await page.mouse.move(sourceBox!.x + sourceBox!.width / 2, sourceBox!.y + sourceBox!.height / 2)
    await page.mouse.down()
    await page.mouse.move(targetBox!.x + targetBox!.width / 2, targetBox!.y + targetBox!.height / 2, { steps: 16 })
    await page.mouse.up()

    await page.waitForTimeout(250)
    await expect(page.locator('.react-flow__edge')).toHaveCount(0)
  })

  test('viewport state persists after pan/zoom without node edits', async ({ page }) => {
    await createNode(page, 'text')

    const flow = page.locator('.react-flow')
    const flowBox = await flow.boundingBox()
    expect(flowBox).not.toBeNull()

    const centerX = flowBox!.x + flowBox!.width / 2
    const centerY = flowBox!.y + flowBox!.height / 2

    await page.mouse.move(centerX, centerY)
    await page.mouse.down()
    await page.mouse.move(centerX + 220, centerY + 140, { steps: 14 })
    await page.mouse.up()
    await flow.hover()
    await page.mouse.wheel(0, -960)
    await page.waitForTimeout(240)

    const beforeReloadNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    const beforeReloadBox = await beforeReloadNode.boundingBox()
    expect(beforeReloadBox).not.toBeNull()

    const persistedViewport = await page.evaluate(() => {
      const raw = window.localStorage.getItem('infinite-canvas-flow')
      if (!raw) return null
      const parsed = JSON.parse(raw) as { viewport?: { x: unknown; y: unknown; zoom: unknown } }
      const viewport = parsed.viewport
      if (!viewport) return null
      if (typeof viewport.x !== 'number' || typeof viewport.y !== 'number' || typeof viewport.zoom !== 'number') return null
      return viewport
    })
    expect(persistedViewport).not.toBeNull()

    await page.reload()
    await page.waitForSelector('.react-flow', { timeout: 30000 })

    const afterReloadNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    const afterReloadBox = await afterReloadNode.boundingBox()
    expect(afterReloadBox).not.toBeNull()
    expect(Math.abs(afterReloadBox!.x - beforeReloadBox!.x)).toBeLessThan(24)
    expect(Math.abs(afterReloadBox!.y - beforeReloadBox!.y)).toBeLessThan(24)
  })

  test('manual node size from persisted state is not overridden by stable height', async ({ page }) => {
    await createNode(page, 'image')

    await page.evaluate(() => {
      const raw = window.localStorage.getItem('infinite-canvas-flow')
      if (!raw) return

      const parsed = JSON.parse(raw) as {
        version: number
        nodes: Array<Record<string, unknown>>
        edges: Array<Record<string, unknown>>
        viewport?: { x: number; y: number; zoom: number }
      }

      const nextNodes = parsed.nodes.map((node) => {
        const nodeType = typeof node.type === 'string' ? node.type : ''
        if (nodeType !== 'image-node') return node

        const data = typeof node.data === 'object' && node.data !== null ? node.data as Record<string, unknown> : {}
        const style = typeof node.style === 'object' && node.style !== null ? node.style as Record<string, unknown> : {}

        return {
          ...node,
          data: {
            ...data,
            h: 520,
            manualSize: true,
            mediaWidth: 1280,
            mediaHeight: 720,
          },
          style: {
            ...style,
            height: 520,
          },
        }
      })

      window.localStorage.setItem('infinite-canvas-flow', JSON.stringify({ ...parsed, nodes: nextNodes }))
    })

    await page.reload()
    await page.waitForSelector('.react-flow', { timeout: 30000 })

    const imageNode = page.locator('[data-testid^="rf__node-image-node"]').first()
    const box = await imageNode.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.height).toBeGreaterThan(500)
  })

  test('deleting selected edge removes connection', async ({ page }) => {
    test.setTimeout(60000)
    await createNodeAt(page, 'text', 0.32, 0.42)
    await createNodeAt(page, 'video', 0.7, 0.42)

    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    const videoNode = page.locator('[data-testid^="rf__node-video-node"]').first()
    await textNode.locator('[data-testid="text-preview-frame"]').dblclick({ force: true })
    const editor = textNode.getByLabel('text node editor')
    await editor.fill('delete edge')
    await editor.blur()

    const sourcePort = textNode.getByLabel('text-node-output-port')
    const targetFrame = await videoNode.locator('[data-preview-frame="video"]').boundingBox()
    const sourceBox = await sourcePort.boundingBox()
    expect(sourceBox).not.toBeNull()
    expect(targetFrame).not.toBeNull()

    await page.mouse.move(sourceBox!.x + sourceBox!.width / 2, sourceBox!.y + sourceBox!.height / 2)
    await page.mouse.down()
    await page.mouse.move(targetFrame!.x + 24, targetFrame!.y + targetFrame!.height / 2, { steps: 16 })
    await page.mouse.up()

    await expect(page.locator('.react-flow__edge')).toHaveCount(1, { timeout: 10000 })
    await page.getByRole('button', { name: 'delete edge' }).first().click({ force: true })
    await expect(page.locator('.react-flow__edge')).toHaveCount(0)
  })

  test('deleting a connected node removes its edges', async ({ page }) => {
    test.setTimeout(60000)
    await createNodeAt(page, 'text', 0.32, 0.38)
    await createNodeAt(page, 'image', 0.7, 0.46)

    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    const imageNode = page.locator('[data-testid^="rf__node-image-node"]').first()
    await textNode.locator('[data-testid="text-preview-frame"]').dblclick({ force: true })
    const editor = textNode.getByLabel('text node editor')
    await editor.fill('delete connected node')
    await editor.blur()

    const sourcePort = textNode.getByLabel('text-node-output-port')
    const targetFrame = await imageNode.locator('[data-preview-frame="image"]').boundingBox()
    const sourceBox = await sourcePort.boundingBox()
    expect(sourceBox).not.toBeNull()
    expect(targetFrame).not.toBeNull()

    await page.mouse.move(sourceBox!.x + sourceBox!.width / 2, sourceBox!.y + sourceBox!.height / 2)
    await page.mouse.down()
    await page.mouse.move(targetFrame!.x + 24, targetFrame!.y + targetFrame!.height / 2, { steps: 16 })
    await page.mouse.up()

    await expect(page.locator('.react-flow__edge')).toHaveCount(1, { timeout: 10000 })

    await textNode.click()
    await textNode.getByRole('button', { name: 'delete text node' }).click({ force: true })

    await expect(page.locator('[data-testid^="rf__node-text-node"]')).toHaveCount(0)
    await expect(page.locator('.react-flow__edge')).toHaveCount(0)
    await expect(imageNode).toHaveCount(1)
  })

  test('video generation no longer records placeholder success', async ({ page }) => {
    await page.route('**/api/generate-video**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          provider: 'openrouter',
          videos: ['https://example.com/generated-video.mp4'],
        }),
      })
    })

    await createNode(page, 'video')
    const videoNode = page.locator('[data-testid^="rf__node-video-node"]').first()
    await videoNode.click()

    const prompt = videoNode.getByPlaceholder('描述任何你想要生成的视频内容')
    await prompt.fill('generated video prompt')

    const generationResponse = page.waitForResponse((response) =>
      response.url().includes('/api/generate-video') && response.request().method() === 'POST'
    )

    await videoNode.getByRole('button', { name: '生成视频' }).click()
    await generationResponse

    await page.getByRole('button', { name: '生成记录' }).click()
    await expect(page.getByText('done', { exact: true })).toBeVisible()
    await expect(page.locator('div').filter({ hasText: /^generated video prompt$/ }).first()).toBeVisible()
    await expect(page.getByText('unsupported', { exact: true })).toHaveCount(0)
  })

  test('double-click on empty canvas opens add-node menu and creates node', async ({ page }) => {
    const flow = page.locator('.react-flow')
    const flowBox = await flow.boundingBox()
    expect(flowBox).not.toBeNull()

    // Double-click on empty canvas area (bottom-right, away from existing nodes)
    const clickX = flowBox!.x + flowBox!.width * 0.8
    const clickY = flowBox!.y + flowBox!.height * 0.8

    await page.mouse.dblclick(clickX, clickY)

    // Verify the context menu appears
    await expect(page.getByTestId('canvas-context-menu')).toBeVisible()

    // Get initial text node count
    const initialTextNodes = await page.locator('[data-testid^="rf__node-text-node"]').count()

    // Click on text node option in the menu
    await page.getByText('文本', { exact: true }).click()

    // Verify menu closes
    await expect(page.getByTestId('canvas-context-menu')).not.toBeVisible()

    // Verify a new text node was created
    await expect(page.locator('[data-testid^="rf__node-text-node"]')).toHaveCount(initialTextNodes + 1)

    // Verify node was created near the double-click position
    const newNode = page.locator('[data-testid^="rf__node-text-node"]').last()
    const nodeBox = await newNode.boundingBox()
    expect(nodeBox).not.toBeNull()

    // The node should be reasonably close to where we double-clicked
    const nodeCenterX = nodeBox!.x + nodeBox!.width / 2
    const nodeCenterY = nodeBox!.y + nodeBox!.height / 2
    expect(Math.abs(nodeCenterX - clickX)).toBeLessThan(200)
    expect(Math.abs(nodeCenterY - clickY)).toBeLessThan(200)
  })

  test('double-click on existing node does not open menu', async ({ page }) => {
    await createNode(page, 'text')

    // Ensure any existing menu is closed
    await page.mouse.click(0, 0)
    await page.waitForTimeout(100)

    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    const nodeBox = await textNode.boundingBox()
    expect(nodeBox).not.toBeNull()

    // Double-click on the node itself
    const centerX = nodeBox!.x + nodeBox!.width / 2
    const centerY = nodeBox!.y + nodeBox!.height / 2
    await page.mouse.dblclick(centerX, centerY)

    // Menu should not appear
    await expect(page.getByTestId('canvas-context-menu')).not.toBeVisible()
  })

  test('text node has side handles but no top/bottom middle handles', async ({ page }) => {
    await createNode(page, 'text')
    const textNode = page.locator('[data-testid^="rf__node-text-node"]').first()
    await textNode.click()

    // Side handles should be present
    await expect(textNode.getByLabel('text-node-input-port')).toBeVisible()
    await expect(textNode.getByLabel('text-node-output-port')).toBeVisible()

    // Top/bottom middle handles should NOT be present
    const topHandle = textNode.locator('[data-handleid="top-target"]')
    const bottomHandle = textNode.locator('[data-handleid="bottom-source"]')
    await expect(topHandle).toHaveCount(0)
    await expect(bottomHandle).toHaveCount(0)
  })

  test('image node has side handles but no top/bottom middle handles', async ({ page }) => {
    await createNode(page, 'image')
    const imageNode = page.locator('[data-testid^="rf__node-image-node"]').first()
    await imageNode.click()

    // Side handles should be present
    await expect(imageNode.getByLabel('image-node-input-port')).toBeVisible()
    await expect(imageNode.getByLabel('image-node-output-port')).toBeVisible()

    // Top/bottom middle handles should NOT be present
    const topHandle = imageNode.locator('[data-handleid="top-target"]')
    const bottomHandle = imageNode.locator('[data-handleid="bottom-source"]')
    await expect(topHandle).toHaveCount(0)
    await expect(bottomHandle).toHaveCount(0)
  })

  test('video node has side handles but no top/bottom middle handles', async ({ page }) => {
    await createNode(page, 'video')
    const videoNode = page.locator('[data-testid^="rf__node-video-node"]').first()
    await videoNode.click()

    // Side handles should be present
    await expect(videoNode.getByLabel('video-node-input-port')).toBeVisible()
    await expect(videoNode.getByLabel('video-node-output-port')).toBeVisible()

    // Top/bottom middle handles should NOT be present
    const topHandle = videoNode.locator('[data-handleid="top-target"]')
    const bottomHandle = videoNode.locator('[data-handleid="bottom-source"]')
    await expect(topHandle).toHaveCount(0)
    await expect(bottomHandle).toHaveCount(0)
  })

  test('image node remove button clears media', async ({ page }) => {
    await page.route('**/api/upload', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          filename: 'test-image.png',
          content_type: 'image/png',
          size: 1024,
          data_url: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        }),
      })
    })

    await createNode(page, 'image')
    const imageNode = page.locator('[data-testid^="rf__node-image-node"]').first()
    await imageNode.click()

    // Upload an image
    const uploadButton = imageNode.getByRole('button', { name: '上传' })
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      uploadButton.click(),
    ])
    await chooser.setFiles({
      name: 'test.png',
      mimeType: 'image/png',
      buffer: Buffer.from('fake-image-payload'),
    })

    // Wait for image to appear
    const img = imageNode.getByTestId('image-node-preview-media')
    await expect(img).toBeVisible()

    // Click remove button
    const removeButton = imageNode.getByRole('button', { name: 'remove image' })
    await expect(removeButton).toBeVisible()
    await removeButton.click()

    // Image should be gone, placeholder should be visible
    await expect(img).not.toBeVisible()
    await expect(imageNode.locator('[data-preview-frame="image"] .lucide-image.h-8')).toBeVisible()
  })
})

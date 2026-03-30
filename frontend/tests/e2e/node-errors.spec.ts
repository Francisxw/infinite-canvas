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

async function createNode(page: import('@playwright/test').Page, type: 'image' | 'video') {
  await page.getByRole('button', { name: '新建节点' }).click()
  await expect(page.getByTestId('dock-create-panel')).toBeVisible()

  if (type === 'image') {
    await page.getByTestId('dock-create-image').click()
    return
  }

  await page.getByTestId('dock-create-video').click()
}

async function registerAccount(page: import('@playwright/test').Page) {
  await page.getByRole('button', { name: '个人中心' }).click()
  await page.getByRole('button', { name: '注册' }).click()
  const seed = Date.now().toString().slice(-6)
  await page.getByLabel('昵称').fill(`E2E${seed}`)
  await page.getByLabel('邮箱').fill(`e2e${seed}@example.com`)
  await page.getByLabel('密码').fill('secret123')
  await page.getByRole('button', { name: '创建账户并进入工作台' }).click()
  await expect(page.getByRole('button', { name: '总览' })).toBeVisible({ timeout: 15000 })
}

test.describe('Node error handling', () => {
  test('upload failure shows a visible error message', async ({ page }) => {
    await page.route('**/api/upload', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'upload_failed',
            message: '图像上传失败，请稍后重试。',
          },
        }),
      })
    })

    await resetCanvas(page)
    await createNode(page, 'image')

    const imageNode = page.locator('[data-testid^="rf__node-image-node"]').first()
    await imageNode.click()

    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      imageNode.getByRole('button', { name: '上传' }).click(),
    ])

    await chooser.setFiles({
      name: 'broken-image.png',
      mimeType: 'image/png',
      buffer: Buffer.from('not-a-real-png'),
    })

    await expect(imageNode.getByRole('alert')).toContainText('图像上传失败，请稍后重试。')
  })

  test('model loading failure keeps fallback UI available', async ({ page }) => {
    await page.route('**/api/models**', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'models_unavailable',
            message: '模型加载失败，请稍后重试。',
          },
        }),
      })
    })

    await resetCanvas(page)
    await createNode(page, 'image')

    const imageNode = page.locator('[data-testid^="rf__node-image-node"]').first()
    await imageNode.click()

    await expect(imageNode.getByRole('alert')).toContainText('模型加载失败，请稍后重试。')
    await expect(imageNode.getByText('Banana 2')).toBeVisible()
  })

  test('image generation continues after node loses selection', async ({ page }) => {
    await page.route('**/api/generate-image**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 360))
      const imageDataUrl = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7fJxUAAAAASUVORK5CYII='
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          provider: 'openrouter',
          choices: [
            {
              message: {
                images: [{ url: imageDataUrl }],
              },
            },
          ],
        }),
      })
    })

    await resetCanvas(page)
    await createNode(page, 'image')

    const imageNode = page.locator('[data-testid^="rf__node-image-node"]').first()
    await imageNode.click()
    const prompt = imageNode.getByPlaceholder('描述任何你想要生成的图像内容')
    await prompt.fill('a small red dot')

    const generationResponse = page.waitForResponse((response) =>
      response.url().includes('/api/generate-image') && response.request().method() === 'POST'
    )

    await imageNode.getByRole('button', { name: '生成图像' }).click()

    await page.locator('.react-flow__pane').click({ position: { x: 24, y: 24 } })
    await generationResponse

    await page.getByRole('button', { name: '生成记录' }).click()
    await page.getByRole('button', { name: '全部' }).click()
    await expect(page.getByText('已完成: 1')).toBeVisible({ timeout: 12000 })
    await expect(page.getByText('cancelled', { exact: true })).toHaveCount(0)
  })

  test('video generation failure shows a visible error message', async ({ page }) => {
    await page.route('**/api/generate-video**', async (route) => {
      await route.fulfill({
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'openrouter_video_generation_unsupported',
            message: '视频生成暂时不可用，请稍后重试。',
          },
        }),
      })
    })

    await resetCanvas(page)
    await registerAccount(page)
    await createNode(page, 'video')

    const videoNode = page.locator('[data-testid^="rf__node-video-node"]').first()
    await videoNode.click()

    const prompt = videoNode.getByPlaceholder('描述任何你想要生成的视频内容')
    await prompt.fill('storm over a chrome lake')

    await videoNode.getByRole('button', { name: '生成视频' }).click()

    await expect(videoNode.getByRole('alert')).toContainText('视频生成暂时不可用，请稍后重试。')
  })
})

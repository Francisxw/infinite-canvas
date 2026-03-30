import { chromium } from '@playwright/test'
import fs from 'node:fs/promises'

const FRONTEND_URL = 'http://localhost:5180'
const uploadImagePath = 'D:/个人项目/pp/631b4a67-c05a-430a-b32c-8c6375fa22de.png'
const outputDir = 'D:/个人项目/pp/infinite-canvas/frontend/tmp-output'

async function ensureDir(path) {
  await fs.mkdir(path, { recursive: true })
}

async function main() {
  await ensureDir(outputDir)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } })
  const apiEvents = []
  const requestEvents = []

  page.on('response', async (response) => {
    if (!response.url().includes('/api/generate-image')) return
    let body = null
    try {
      body = await response.json()
    } catch {
      body = await response.text().catch(() => null)
    }
    apiEvents.push({
      url: response.url(),
      status: response.status(),
      body,
    })
  })

  page.on('request', (request) => {
    if (!request.url().includes('/api/generate-image')) return
    requestEvents.push({
      url: request.url(),
      method: request.method(),
      postData: request.postData(),
    })
  })

  await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' })

  const imageNode = page.locator('.react-flow__node').filter({ hasText: 'Image' }).first()
  await imageNode.waitFor({ state: 'visible', timeout: 30000 })

  const uploadButton = imageNode.getByRole('button', { name: '上传' }).first()
  const fileChooserPromise = page.waitForEvent('filechooser')
  await uploadButton.click()
  const fileChooser = await fileChooserPromise
  await fileChooser.setFiles(uploadImagePath)

  const previewImage = imageNode.locator('img').first()
  await previewImage.waitFor({ state: 'visible', timeout: 30000 })
  const uploadedSrc = await previewImage.getAttribute('src')

  await page.screenshot({ path: `${outputDir}/image-node-after-upload.png`, fullPage: true })

  const promptArea = imageNode.locator('textarea').first()
  await promptArea.fill('a cat')

  const modelSelect = imageNode.locator('select').first()
  await modelSelect.selectOption('google/gemini-3.1-flash-image-preview')

  const footerButtons = imageNode.locator('button')
  const buttonCount = await footerButtons.count()
  const buttonDescriptions = []
  for (let index = 0; index < buttonCount; index += 1) {
    const button = footerButtons.nth(index)
    buttonDescriptions.push({
      index,
      text: (await button.textContent())?.trim() ?? '',
      aria: await button.getAttribute('aria-label'),
    })
  }

  const generateButton = footerButtons.last()
  const generationResponsePromise = page.waitForResponse(
    (response) => response.url().includes('/api/generate-image') && response.status() === 200,
    { timeout: 240000 }
  )
  await generateButton.click()
  await generationResponsePromise

  let generationChanged = false
  let generatedSrc = uploadedSrc

  try {
    await page.waitForFunction(
      (previousSrc) => {
        const nodes = Array.from(document.querySelectorAll('.react-flow__node'))
        const imageNodeEl = nodes.find((node) => node.textContent?.includes('Image'))
        const img = imageNodeEl?.querySelector('img')
        const currentSrc = img?.getAttribute('src')
        return typeof currentSrc === 'string' && currentSrc.length > 0 && currentSrc !== previousSrc
      },
      uploadedSrc,
      { timeout: 240000 }
    )

    generatedSrc = await previewImage.getAttribute('src')
    generationChanged = Boolean(generatedSrc && uploadedSrc && generatedSrc !== uploadedSrc)
  } catch {
    generationChanged = false
  }

  await page.screenshot({ path: `${outputDir}/image-node-after-generate.png`, fullPage: true })

  const summary = {
    uploadedSrcPrefix: uploadedSrc?.slice(0, 80) ?? null,
    generatedSrcPrefix: generatedSrc?.slice(0, 80) ?? null,
    uploadedSrcLength: uploadedSrc?.length ?? 0,
    generatedSrcLength: generatedSrc?.length ?? 0,
    generationChanged,
    buttonDescriptions,
    requestEvents,
    apiEvents,
  }

  await fs.writeFile(`${outputDir}/verify-media-node.json`, JSON.stringify(summary, null, 2), 'utf8')
  await browser.close()

  console.log(JSON.stringify(summary, null, 2))
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})

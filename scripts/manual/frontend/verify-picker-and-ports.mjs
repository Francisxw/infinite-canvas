import { chromium } from '@playwright/test'
import fs from 'node:fs/promises'

const FRONTEND_URL = 'http://localhost:5180'
const outputDir = 'D:/个人项目/pp/infinite-canvas/frontend/tmp-output'

async function ensureDir(path) {
  await fs.mkdir(path, { recursive: true })
}

async function main() {
  await ensureDir(outputDir)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } })
  await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' })

  const imageNode = page.locator('.react-flow__node').filter({ hasText: 'Image' }).first()
  const videoNode = page.locator('.react-flow__node').filter({ hasText: 'Video' }).first()
  await imageNode.waitFor({ state: 'visible', timeout: 30000 })
  await videoNode.waitFor({ state: 'visible', timeout: 30000 })

  const idleLeftPortVisible = await imageNode.locator('.react-flow__handle-left').isVisible()
  const idleRightPortVisible = await imageNode.locator('.react-flow__handle-right').isVisible()

  await imageNode.click()
  await page.waitForTimeout(250)

  const previewBox = await imageNode.locator('[data-preview-frame="image"]').boundingBox()
  const drawerTextarea = imageNode.locator('textarea')
  const drawerBox = await drawerTextarea.boundingBox()

  await imageNode.getByText(/Banana|GPT-5|Flux|Riverflow/).first().click()
  const picker = page.locator('.max-h-72').first()
  const pickerScrollable = await picker.evaluate((el) => el.scrollHeight > el.clientHeight)
  const addedModelVisible = await page.getByText(/Flux 2 Klein 4B|Seedream 4.5/).first().isVisible().catch(() => false)

  const idleProviderTextCount = await page.getByText(/Google:|OpenRouter 当前未公开该模型|OpenRouter 当前未公开视频输出模型/).count()

  const imageDrawerWiderThanPreview = Boolean(previewBox && drawerBox && drawerBox.width > previewBox.width)
  const imageDrawerCloseToPreview = Boolean(previewBox && drawerBox && drawerBox.y - (previewBox.y + previewBox.height) < 24)

  await page.keyboard.press('Escape').catch(() => {})
  await page.mouse.click(30, 30)

  await videoNode.click()
  await page.waitForTimeout(250)
  const videoIdleProviderCount = await videoNode.getByText(/OpenRouter 当前未公开视频输出模型|Google:/).count()

  const summary = {
    imageIdlePortsVisible: idleLeftPortVisible && idleRightPortVisible,
    imageDrawerWiderThanPreview,
    imageDrawerCloseToPreview,
    imagePickerScrollable: pickerScrollable,
    addedImageModelsVisible: addedModelVisible,
    idleProviderTextHidden: idleProviderTextCount === 0,
    videoIdleProviderTextHidden: videoIdleProviderCount === 0,
  }

  await page.screenshot({ path: `${outputDir}/picker-and-ports.png`, fullPage: true })
  await fs.writeFile(`${outputDir}/verify-picker-and-ports.json`, JSON.stringify(summary, null, 2), 'utf8')
  console.log(JSON.stringify(summary, null, 2))
  await browser.close()
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})

import { chromium } from '@playwright/test'
import fs from 'node:fs/promises'

const FRONTEND_URL = 'http://localhost:5180'
const outputDir = 'D:/个人项目/pp/infinite-canvas/frontend/tmp-output'

async function ensureDir(path) {
  await fs.mkdir(path, { recursive: true })
}

function sameCenter(boxA, boxB, tolerance = 2) {
  if (!boxA || !boxB) return false
  const centerAX = boxA.x + boxA.width / 2
  const centerAY = boxA.y + boxA.height / 2
  const centerBX = boxB.x + boxB.width / 2
  const centerBY = boxB.y + boxB.height / 2
  return Math.abs(centerAX - centerBX) <= tolerance && Math.abs(centerAY - centerBY) <= tolerance
}

async function main() {
  await ensureDir(outputDir)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } })

  await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' })

  const imageNode = page.locator('.react-flow__node').filter({ hasText: 'Image' }).first()
  const videoNode = page.locator('.react-flow__node').filter({ hasText: 'Video' }).first()
  const textNode = page.locator('.react-flow__node').filter({ hasText: 'Text' }).first()

  await imageNode.waitFor({ state: 'visible', timeout: 30000 })
  await videoNode.waitFor({ state: 'visible', timeout: 30000 })
  await textNode.waitFor({ state: 'visible', timeout: 30000 })

  const imageButtons = imageNode.locator('button')
  const videoButtons = videoNode.locator('button')
  const textButtons = textNode.locator('button')

  const imageButtonTexts = []
  for (let i = 0; i < (await imageButtons.count()); i += 1) imageButtonTexts.push((await imageButtons.nth(i).textContent())?.trim() ?? '')
  const videoButtonTexts = []
  for (let i = 0; i < (await videoButtons.count()); i += 1) videoButtonTexts.push((await videoButtons.nth(i).textContent())?.trim() ?? '')
  const textButtonTexts = []
  for (let i = 0; i < (await textButtons.count()); i += 1) textButtonTexts.push((await textButtons.nth(i).textContent())?.trim() ?? '')

  const imageUploadPill = imageNode.getByRole('button', { name: '上传' }).first()
  const videoUploadPill = videoNode.getByRole('button', { name: '上传' }).first()
  const imageDeleteButton = imageNode.getByLabel(/delete image node/i)

  const imageNodeBox = await imageNode.boundingBox()
  const imagePillBox = await imageUploadPill.boundingBox()
  const imageHandleCircle = imageNode.locator('span').filter({ hasText: '+' }).first()
  const imageHandleBox = await imageHandleCircle.boundingBox()
  const imageHandleParent = imageNode.locator('.react-flow__handle-left').first()
  const imageHandleParentBox = await imageHandleParent.boundingBox()

  await page.click('.react-flow__pane', { position: { x: 40, y: 40 } })
  await page.click('.react-flow__pane', { button: 'right', position: { x: 260, y: 220 } })
  const contextMenu = page.locator('text=Canvas').locator('..')
  await contextMenu.waitFor({ state: 'visible', timeout: 10000 })
  const deleteMenuButton = page.getByText('删除选中节点').first()
  const contextMenuVisible = await contextMenu.isVisible()
  const deleteMenuButtonVisible = await deleteMenuButton.isVisible()
  await page.keyboard.press('Escape').catch(() => {})
  await page.mouse.click(40, 40)

  await imageNode.hover()
  await imageDeleteButton.click()
  await imageNode.waitFor({ state: 'detached', timeout: 10000 })

  await page.screenshot({ path: `${outputDir}/node-ui-verification.png`, fullPage: true })

  const summary = {
    imageUploadPillAboveNode: Boolean(imageNodeBox && imagePillBox && imagePillBox.y + imagePillBox.height <= imageNodeBox.y + 8),
    imageUploadPillTopCentered: Boolean(imageNodeBox && imagePillBox && Math.abs((imageNodeBox.x + imageNodeBox.width / 2) - (imagePillBox.x + imagePillBox.width / 2)) <= 3),
    videoUploadPillExists: await videoUploadPill.isVisible(),
    imageTextareaHasInlineUploadButton: imageButtonTexts.filter((text) => text === '上传').length > 1,
    videoTextareaHasInlineUploadButton: videoButtonTexts.filter((text) => text === '上传').length > 1,
    textNodeHasUploadButton: textButtonTexts.some((text) => text === '上传'),
    handlePlusCenteredInCircle: sameCenter(imageHandleBox, imageHandleParentBox),
    contextMenuVisible,
    deleteMenuButtonVisible,
    imageDeleteWorked: (await page.locator('.react-flow__node').filter({ hasText: 'Image' }).count()) === 0,
    imageNodeOpacity: await textNode.evaluate((node) => getComputedStyle(node).opacity),
  }

  await fs.writeFile(`${outputDir}/verify-node-ui.json`, JSON.stringify(summary, null, 2), 'utf8')
  console.log(JSON.stringify(summary, null, 2))

  await browser.close()
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})

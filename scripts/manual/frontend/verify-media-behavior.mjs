import { chromium } from '@playwright/test'
import fs from 'node:fs/promises'

const FRONTEND_URL = 'http://localhost:5180'
const outputDir = 'D:/个人项目/pp/infinite-canvas/frontend/tmp-output'

async function ensureDir(path) {
  await fs.mkdir(path, { recursive: true })
}

function center(box) {
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 }
}

async function main() {
  await ensureDir(outputDir)

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } })
  await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' })

  const imageNode = page.locator('.react-flow__node').filter({ hasText: 'Image' }).first()
  await imageNode.waitFor({ state: 'visible', timeout: 30000 })

  const edgePath = page.locator('.react-flow__edge-path').first()
  const edgePathD = await edgePath.getAttribute('d')
  const edgeVisibleBefore = Boolean(edgePathD && edgePathD.length > 0)

  const imageNodeBox = await imageNode.boundingBox()
  const previewBox = await imageNode.locator('[data-preview-frame="image"]').boundingBox()
  const leftPortBox = await imageNode.locator('.react-flow__handle-left').boundingBox()
  const rightPortBox = await imageNode.locator('.react-flow__handle-right').boundingBox()

  await imageNode.click()
  await page.waitForTimeout(250)

  const imageNodeSelectedBox = await imageNode.boundingBox()
  const editorTextareaVisible = await imageNode.locator('textarea').isVisible()

  const edgePathDAfter = await edgePath.getAttribute('d')
  const edgeVisibleAfter = Boolean(edgePathDAfter && edgePathDAfter.length > 0)

  const previewCenterY = previewBox ? center(previewBox).y : null
  const leftPortCenterY = leftPortBox ? center(leftPortBox).y : null
  const rightPortCenterY = rightPortBox ? center(rightPortBox).y : null

  const summary = {
    nodeHeightStableOnSelect: Boolean(
      imageNodeBox && imageNodeSelectedBox && Math.abs(imageNodeSelectedBox.height - imageNodeBox.height) <= 2
    ),
    editorRevealsInsideNode: editorTextareaVisible,
    edgeVisibleBeforeSelection: edgeVisibleBefore,
    edgeVisibleAfterSelection: edgeVisibleAfter,
    leftPortCenteredOnPreview: Boolean(previewCenterY && leftPortCenterY && Math.abs(leftPortCenterY - previewCenterY) <= 3),
    rightPortCenteredOnPreview: Boolean(previewCenterY && rightPortCenterY && Math.abs(rightPortCenterY - previewCenterY) <= 3),
    imageNodeHeight: imageNodeBox?.height ?? null,
    imageNodeSelectedHeight: imageNodeSelectedBox?.height ?? null,
    previewCenterY,
    leftPortCenterY,
    rightPortCenterY,
  }

  await page.screenshot({ path: `${outputDir}/media-behavior.png`, fullPage: true })
  await fs.writeFile(`${outputDir}/verify-media-behavior.json`, JSON.stringify(summary, null, 2), 'utf8')
  console.log(JSON.stringify(summary, null, 2))
  await browser.close()
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})

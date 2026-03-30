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
  await imageNode.waitFor({ state: 'visible', timeout: 30000 })

  const idleGenerateCount = await imageNode.getByText('生成').count()
  const idleModelTextVisible = await imageNode.getByText(/Nano Banana|GPT-5 Image|Flux|Riverflow/).count()

  const nodeBoxBefore = await imageNode.boundingBox()
  await imageNode.click()
  await page.waitForTimeout(250)

  const editorTextarea = imageNode.locator('textarea')
  const editorVisible = await editorTextarea.isVisible()
  const editorBox = await editorTextarea.boundingBox()
  const nodeBoxAfter = await imageNode.boundingBox()

  const summary = {
    idleGenerateHidden: idleGenerateCount === 0,
    idleModelHidden: idleModelTextVisible === 0,
    editorVisibleWhenSelected: editorVisible,
    editorAppearsBelowNode: Boolean(nodeBoxAfter && editorBox && editorBox.y > nodeBoxAfter.y + 180),
    nodeHeightStable: Boolean(nodeBoxBefore && nodeBoxAfter && Math.abs(nodeBoxAfter.height - nodeBoxBefore.height) <= 2),
  }

  await page.screenshot({ path: `${outputDir}/editor-reveal.png`, fullPage: true })
  await fs.writeFile(`${outputDir}/verify-editor-reveal.json`, JSON.stringify(summary, null, 2), 'utf8')
  console.log(JSON.stringify(summary, null, 2))
  await browser.close()
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})

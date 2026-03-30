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

  const initialTextCount = await page.locator('.react-flow__node').filter({ hasText: 'Text' }).count()

  await page.dblclick('.react-flow__pane', { position: { x: 1200, y: 420 } })
  await page.getByText('添加文本节点').click()
  await page.waitForTimeout(300)
  const afterAddTextCount = await page.locator('.react-flow__node').filter({ hasText: 'Text' }).count()

  const imageNode = page.locator('.react-flow__node').filter({ hasText: 'Image' }).first()
  await imageNode.click()
  await page.click('.react-flow__pane', { button: 'right', position: { x: 260, y: 220 } })
  const contextDeleteButton = page.getByText('删除选中节点').first()
  const contextDeleteVisible = await contextDeleteButton.isVisible()
  await contextDeleteButton.click()
  await page.waitForTimeout(300)
  const imageRemaining = await page.locator('.react-flow__node').filter({ hasText: 'Image' }).count()

  const summary = {
    addTextNodeWorked: afterAddTextCount === initialTextCount + 1,
    contextDeleteVisible,
    contextDeleteWorked: imageRemaining === 0,
  }

  await fs.writeFile(`${outputDir}/verify-menu-and-delete.json`, JSON.stringify(summary, null, 2), 'utf8')
  console.log(JSON.stringify(summary, null, 2))

  await browser.close()
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})

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
  const textNode = page.locator('.react-flow__node').filter({ hasText: 'Text' }).first()
  await imageNode.waitFor({ state: 'visible', timeout: 30000 })
  await textNode.waitFor({ state: 'visible', timeout: 30000 })

  await imageNode.click()
  await page.waitForTimeout(250)
  await imageNode.getByText(/Banana|Flux|Riverflow|GPT-5|Seedream/).first().click()

  const picker = page.locator('.canvas-scrollbar').first()
  const pickerHasScrollbarClass = (await picker.count()) > 0
  const addedModelVisible = await page.getByText(/Flux 2 Klein 4B|Flux 2 Pro|Flux 2 Flex|Seedream 4.5/).first().isVisible().catch(() => false)

  await page.mouse.click(30, 30)
  await page.waitForTimeout(200)
  const pickerClosed = (await page.locator('.canvas-scrollbar').count()) === 0

  const textToolbar = textNode.locator('button[aria-label="text heading 1"]').first()
  const textArea = textNode.locator('textarea').first()
  const textAreaBorderStyle = await textArea.evaluate((node) => getComputedStyle(node).borderStyle)
  const textToolbarBorderStyle = await textToolbar.evaluate((node) => getComputedStyle(node).borderStyle)

  const summary = {
    pickerUsesCustomScrollbar: pickerHasScrollbarClass,
    addedModelVisible,
    pickerAutoClosedOnOutsideClick: pickerClosed,
    textNodeUsesDashedIdleBorder: textAreaBorderStyle === 'dashed',
    textToolbarPresent: await textToolbar.isVisible(),
    textToolbarButtonBorderStyle: textToolbarBorderStyle,
  }

  await page.screenshot({ path: `${outputDir}/text-and-picker.png`, fullPage: true })
  await fs.writeFile(`${outputDir}/verify-text-and-picker.json`, JSON.stringify(summary, null, 2), 'utf8')
  console.log(JSON.stringify(summary, null, 2))
  await browser.close()
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})

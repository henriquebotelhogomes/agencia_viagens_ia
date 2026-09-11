import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Root screenshots directory: d:\agencia_viagens_ia\screenshots
const screenshotsDir = path.resolve(__dirname, '../../screenshots');
const framesDir = path.resolve(screenshotsDir, 'frames');

if (!fs.existsSync(framesDir)) {
  fs.mkdirSync(framesDir, { recursive: true });
}

async function run() {
  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1.5,
  });
  const page = await context.newPage();

  // 1. Landing Page (Hero + Briefing)
  console.log('1. Capturing Landing Page...');
  await page.goto('http://localhost:3000', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(screenshotsDir, 'landingpage.png') });
  await page.screenshot({ path: path.join(framesDir, 'frame_01.png') });

  // 2. Scroll to Showcase & Destination Cards
  console.log('2. Scrolling to showcase...');
  await page.evaluate(() => window.scrollBy({ top: 380, behavior: 'smooth' }));
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(framesDir, 'frame_02.png') });

  // 3. Click Destination card to populate
  console.log('3. Clicking destination card...');
  const card = await page.$('text=Lisboa');
  if (card) {
    await card.click();
    await page.waitForTimeout(800);
  }
  await page.screenshot({ path: path.join(framesDir, 'frame_03.png') });

  // 4. Execution View (Lisboa)
  console.log('4. Navigating to execution view...');
  const executionId = 'b9eaf2ee-9583-4cbf-a4a2-dd4fc8b40d80';
  await page.goto(`http://localhost:3000/executions/${executionId}`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);

  // result-1: Top execution view (stepper, metrics, header, export selector)
  await page.screenshot({ path: path.join(screenshotsDir, 'result-1.png') });
  await page.screenshot({ path: path.join(framesDir, 'frame_04.png') });

  // result-2: Central de Reservas & Onde Comprar
  console.log('5. Capturing Central de Reservas...');
  const bookingHeader = await page.$('text=Central de Compra');
  if (bookingHeader) {
    await bookingHeader.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(screenshotsDir, 'result-2.png') });
    await page.screenshot({ path: path.join(framesDir, 'frame_05.png') });
  }

  // result-3 & result-4: Vitrine Fotográfica dos Pontos de Interesse & Modal
  console.log('6. Capturing POI Photo Showcase...');
  const poiHeader = await page.$('text=Fotos dos Pontos de Interesse');
  if (poiHeader) {
    await poiHeader.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(screenshotsDir, 'result-3.png') });
    await page.screenshot({ path: path.join(framesDir, 'frame_06.png') });

    // Open POI detail modal
    const poiCard = await page.$('article div.cursor-pointer, article [role="button"]');
    if (poiCard) {
      await poiCard.click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: path.join(screenshotsDir, 'result-4.png') });
      await page.screenshot({ path: path.join(framesDir, 'frame_07.png') });

      // Close modal
      const closeBtn = await page.$('button[aria-label="Fechar"], button:has-text("Fechar")');
      if (closeBtn) {
        await closeBtn.click();
        await page.waitForTimeout(500);
      }
    }
  }

  // result-5: Itinerário dia a dia + Mapa Interativo
  console.log('7. Capturing Itinerary & Interactive Map...');
  const mapEl = await page.$('#mapa-roteiro');
  if (mapEl) {
    await mapEl.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(screenshotsDir, 'result-5.png') });
    await page.screenshot({ path: path.join(framesDir, 'frame_08.png') });
  }

  // Export Select Dropdown
  console.log('8. Selecting PDF in Export dropdown...');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await page.waitForTimeout(800);
  const selectEl = await page.$('select');
  if (selectEl) {
    await selectEl.selectOption('pdf');
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(framesDir, 'frame_09.png') });
  }

  // result-6: Dashboard FinOps
  console.log('9. Capturing FinOps Dashboard...');
  await page.goto('http://localhost:3000/finops', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(screenshotsDir, 'result-6.png') });
  await page.screenshot({ path: path.join(framesDir, 'frame_10.png') });

  await browser.close();
  console.log('Capture finished successfully!');
}

run().catch(err => {
  console.error('Capture failed:', err);
  process.exit(1);
});

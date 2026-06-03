const path = require('path');
const { chromium } = require('../../slides/node_modules/playwright-chromium');

(async () => {
  const htmlPath = path.resolve(__dirname, 'voicephishing-rag-final-report.html');
  const pdfPath = path.resolve(__dirname, 'voicephishing-rag-final-report.pdf');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1240, height: 1754 }, deviceScaleFactor: 1 });
  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle' });
  await page.emulateMedia({ media: 'print' });
  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: '0mm', right: '0mm', bottom: '0mm', left: '0mm' }
  });
  await browser.close();
  console.log(pdfPath);
})();

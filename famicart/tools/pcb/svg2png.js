// node svg2png.js in.svg out.png [scale]   - rasterise an SVG with headless Chromium (needs the 'playwright' package and its Chromium)
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [inp, out, scale] = process.argv.slice(2);
  const svg = fs.readFileSync(inp, 'utf8');
  const m = svg.match(/width="(\d+)" height="(\d+)"/);
  const w = parseInt(m[1]), h = parseInt(m[2]);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: parseFloat(scale || '2') });
  await page.setContent('<html><body style="margin:0;background:#fff">' + svg + '</body></html>');
  await page.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
  await browser.close();
  console.log('png', out, w, 'x', h);
})();

// Renders each slide of slides.html to a PNG (2560x1440) for build_pptx.py. Usage: node render_pngs.js <out_dir>
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
  await p.goto('file://' + process.cwd() + '/slides.html'); await p.waitForLoadState('networkidle');
  const n = await p.locator('section').count();
  for (let i = 0; i < n; i++) {
    await p.locator('section').nth(i).screenshot({ path: `${out}/slide-${i + 1}.png` });
  }
  await b.close();
  console.log(n, 'slides rendered');
})();

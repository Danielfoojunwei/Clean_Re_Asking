const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + process.cwd() + '/paper.html'); await p.waitForLoadState('networkidle');
  await p.pdf({ path: process.argv[2], format: 'A4', printBackground: true, displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:8px;color:#666;width:100%;text-align:center;font-family:Inter,sans-serif"><span class="pageNumber"></span></div>',
    margin: { top: '17mm', bottom: '18mm', left: '17mm', right: '17mm' } });
  await b.close();
})();

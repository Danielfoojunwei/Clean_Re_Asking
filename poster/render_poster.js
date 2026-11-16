// Renders poster.html (3000 x 2121 CSS px) to Clean_Reasking_Poster.pdf (A0 landscape) and Clean_Reasking_Poster.png
// (4800 x 3394), and reports any card or column whose content does not fit. Run from poster/.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 3000, height: 2121 }, deviceScaleFactor: 1.6 });
  await p.goto('file://' + process.cwd() + '/poster.html'); await p.waitForLoadState('networkidle');
  const fit = await p.evaluate(() => {
    const out = [];
    const footTop = document.querySelector('.foot').getBoundingClientRect().top;
    document.querySelectorAll('.col').forEach((c, i) => {
      const last = c.lastElementChild.getBoundingClientRect();
      out.push(`col ${i + 1}: content ${Math.round(c.scrollHeight)} / ${Math.round(c.clientHeight)} px, last card ends ${Math.round(last.bottom)} (footer at ${Math.round(footTop)})`);
    });
    document.querySelectorAll('.card, .fc, .test, .ev, .fb, .lr, .hb').forEach((e) => {
      if (e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1)
        out.push(`OVERFLOW ${e.className}: ${e.scrollWidth}x${e.scrollHeight} in ${e.clientWidth}x${e.clientHeight} :: ${e.textContent.trim().slice(0, 50)}`);
    });
    return out;
  });
  console.log(fit.join('\n'));
  await p.screenshot({ path: 'Clean_Reasking_Poster.png', fullPage: false });
  await p.pdf({ path: 'Clean_Reasking_Poster.pdf', width: '1189mm', height: '841mm', printBackground: true, scale: 1189 / 25.4 * 96 / 3000,
                margin: { top: 0, bottom: 0, left: 0, right: 0 }, pageRanges: '1' });
  await b.close();
  console.log('poster rendered');
})();

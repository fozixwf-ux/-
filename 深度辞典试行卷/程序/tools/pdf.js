const { chromium } = require('playwright');
(async () => {
  const [,, input, output] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + input, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const opts = {
    path: output, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<div style="width:100%;font-size:7px;color:#8a8070;padding:0 17mm;font-family:GL Noto Serif CJK SC;display:flex;justify-content:space-between"><span>' + (process.env.HDR_L || '格鲁派密续名相辞汇') + '</span><span>' + (process.env.HDR_R || 'Geluk Tantric Glossary') + '</span></div>',
    footerTemplate: '<div style="width:100%;text-align:center;font-size:8px;color:#6b645a;font-family:Noto Serif"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
    outline: true, tagged: false,
  };
  try { await page.pdf(opts); } catch (e) { console.error('retry without outline:', e.message); delete opts.outline; delete opts.tagged; await page.pdf(opts); }
  await browser.close();
})();

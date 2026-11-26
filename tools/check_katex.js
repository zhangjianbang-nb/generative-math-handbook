const puppeteer = require('/home/whu/workspace/servers/chatgpt-browser/node_modules/puppeteer-core');
const base = '/home/whu/workspace/ai_workspace/generative-math-handbook-20261125/site/book/';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/snap/bin/chromium', headless: true, pipe: true,
    userDataDir: '/home/whu/tmp-cr-book-katex', args: ['--no-sandbox', '--disable-gpu']
  });
  const page = await browser.newPage();
  page.setDefaultNavigationTimeout(120000);
  const errs = [], errTexts = [];
  let total = 0;
  const list = process.argv[2] ? process.argv[2].split(',').map(Number) : Array.from({ length: 25 }, (_, k) => k + 1);
  for (const i of list) {
    await page.goto(`file://${base}ch-${i}.html`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => document.querySelectorAll('.katex').length > 0 || document.querySelectorAll('article.sec').length === 0, { timeout: 60000 }).catch(() => {});
    const r = await page.evaluate(() => {
      const e = [...document.querySelectorAll('.katex-error')];
      return { total: document.querySelectorAll('.katex').length, errs: e.length, first: e.slice(0, 2).map(x => x.textContent.slice(0, 120)) };
    });
    total += r.total;
    if (r.errs) { errs.push([i, r.errs]); errTexts.push(...r.first); }
  }
  console.log(JSON.stringify({ katexTotal: total, chaptersWithErrors: errs, sampleErrors: errTexts.slice(0, 6) }, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });

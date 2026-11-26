const puppeteer = require('/home/whu/workspace/servers/chatgpt-browser/node_modules/puppeteer-core');
const base = '/home/whu/workspace/ai_workspace/generative-math-handbook-20261125/site/book/';
const out = base + 'shots/';
const fs = require('fs');
if (!fs.existsSync(out)) fs.mkdirSync(out);

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/snap/bin/chromium',
    headless: true,
    pipe: true,
    userDataDir: '/home/whu/tmp-cr-book-shots',
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars']
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

  await page.setViewport({ width: 1440, height: 980, deviceScaleFactor: 1 });
  await page.goto('file://' + base + 'ch-1.html', { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 1800));

  const stats = await page.evaluate(() => {
    const katex = document.querySelectorAll('.katex').length;
    const arts = document.querySelectorAll('article.sec').length;
    const figs = document.querySelectorAll('figure.fig').length;
    const tables = document.querySelectorAll('.table-wrap table').length;
    const sideW = Math.round(document.getElementById('side').getBoundingClientRect().width);
    const overflowX = document.documentElement.scrollWidth > window.innerWidth + 1;
    const title = document.querySelector('h1').textContent.trim();
    return { katex, arts, figs, tables, sideW, overflowX, title };
  });
  console.log('DESKTOP ' + JSON.stringify(stats));

  await page.screenshot({ path: out + 'book-1-top.png' });

  await page.evaluate(() => {
    document.documentElement.style.scrollBehavior = 'auto';
    const el = document.getElementById('s-1.4');
    if (el) el.scrollIntoView({ block: 'start' });
    window.scrollBy(0, 900);
  });
  await new Promise(r => setTimeout(r, 700));
  await page.screenshot({ path: out + 'book-2-body.png' });

  await page.evaluate(() => {
    const q = document.getElementById('q');
    q.value = '线性';
    q.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await new Promise(r => setTimeout(r, 500));
  const search = await page.evaluate(() => {
    const hits = document.getElementById('hits');
    return { on: hits.classList.contains('on'), n: hits.querySelectorAll('a').length,
             text: document.getElementById('search-status').textContent };
  });
  console.log('SEARCH ' + JSON.stringify(search));
  await page.screenshot({ path: out + 'book-3-search.png' });

  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
  await page.goto('file://' + base + 'ch-1.html', { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 1200));
  const mob = await page.evaluate(() => {
    const overflowX = document.documentElement.scrollWidth > window.innerWidth + 1;
    const td = document.querySelector('.table-wrap td');
    const disp = td ? getComputedStyle(td).display : 'none';
    const side = document.getElementById('side').getBoundingClientRect();
    return { overflowX, tdDisplay: disp, sideVisible: side.left > -10 };
  });
  console.log('MOBILE ' + JSON.stringify(mob));
  await page.screenshot({ path: out + 'book-4-mobile.png' });

  await page.setViewport({ width: 1440, height: 980, deviceScaleFactor: 1 });
  await page.goto('file://' + base + 'index.html', { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 500));
  const idx = await page.evaluate(() => ({
    chapters: document.querySelectorAll('.chaptable tr').length,
    cards: document.querySelectorAll('.pcard').length,
    overflowX: document.documentElement.scrollWidth > window.innerWidth + 1
  }));
  console.log('INDEX ' + JSON.stringify(idx));
  await page.screenshot({ path: out + 'book-5-index.png' });

  console.log('ERRORS ' + JSON.stringify(errors.slice(0, 8)));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });

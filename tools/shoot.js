const puppeteer = require('/home/whu/workspace/servers/chatgpt-browser/node_modules/puppeteer-core');
const path = '/home/whu/workspace/ai_workspace/generative-math-handbook-20261125/site/index.html';
const out = '/home/whu/workspace/ai_workspace/generative-math-handbook-20261125/site';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/snap/bin/chromium',
    headless: 'new',
    pipe: true,
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 980, deviceScaleFactor: 1 });
  await page.goto('file://' + path, { waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 600));

  // 断言：结构计数与布局
  const stats = await page.evaluate(() => {
    const chapters = document.querySelectorAll('.ch').length;
    const units = document.querySelectorAll('details.unit').length;
    const rows = document.querySelectorAll('details.unit tbody tr').length;
    const navLinks = document.querySelectorAll('#nav a').length;
    const sideW = document.getElementById('side').getBoundingClientRect().width;
    const mainL = document.querySelector('main').getBoundingClientRect().left;
    const overflowX = document.documentElement.scrollWidth > window.innerWidth + 1;
    const h1 = document.querySelector('.hero h1').getBoundingClientRect();
    return { chapters, units, rows, navLinks, sideW, mainL, overflowX, h1w: Math.round(h1.width), h1h: Math.round(h1.height) };
  });
  console.log(JSON.stringify(stats));

  await page.screenshot({ path: out + '/shot-1-hero.png' });

  // 关掉平滑滚动，展开第 25 章第 4 编，滚动到该章
  await page.evaluate(() => {
    document.documentElement.style.scrollBehavior = 'auto';
    const ch = document.getElementById('ch-25');
    ch.querySelectorAll('details.unit')[3].open = true;
    ch.scrollIntoView({ block: 'start' });
  });
  await new Promise(r => setTimeout(r, 500));
  await page.screenshot({ path: out + '/shot-2-chapter.png' });

  // 搜索态：输入 score，滚到第一个命中章
  await page.evaluate(() => {
    const q = document.getElementById('search');
    q.value = 'score';
    q.dispatchEvent(new Event('input'));
    const first = document.querySelector('.ch:not(.hidden)');
    if (first) first.scrollIntoView({ block: 'start' });
  });
  await new Promise(r => setTimeout(r, 500));
  const searchStats = await page.evaluate(() => ({
    visibleChapters: [...document.querySelectorAll('.ch')].filter(c => !c.classList.contains('hidden')).length,
    openUnits: [...document.querySelectorAll('details.unit')].filter(u => u.open && !u.classList.contains('hidden')).length,
  }));
  console.log('search:', JSON.stringify(searchStats));
  await page.screenshot({ path: out + '/shot-3-search.png' });

  // 移动端布局断言（不截图）
  await page.setViewport({ width: 390, height: 844 });
  await page.reload({ waitUntil: 'load' });
  await new Promise(r => setTimeout(r, 400));
  const mobile = await page.evaluate(() => {
    const side = document.getElementById('side').getBoundingClientRect();
    const overflow = document.documentElement.scrollWidth > window.innerWidth + 1;
    const tableOverflow = [...document.querySelectorAll('table')].some(t => t.scrollWidth > t.parentElement.clientWidth + 2);
    return { sideStatic: getComputedStyle(document.getElementById('side')).position, sideW: Math.round(side.width), overflow, tableOverflow };
  });
  console.log('mobile:', JSON.stringify(mobile));
  await page.evaluate(() => {
    document.documentElement.style.scrollBehavior = 'auto';
    document.getElementById('ch-25').scrollIntoView({ block: 'start' });
    document.querySelector('#ch-25 details.unit').open = true;
  });
  await new Promise(r => setTimeout(r, 300));
  const mobileTable = await page.evaluate(() => {
    const d = document.querySelector('#ch-25 details.unit');
    const td = d.querySelector('td[data-label]');
    const tr = d.querySelector('tbody tr');
    return {
      tdDisplay: getComputedStyle(td).display,
      before: getComputedStyle(td, '::before').content,
      trH: Math.round(tr.getBoundingClientRect().height),
      tableW: Math.round(d.querySelector('table').getBoundingClientRect().width),
      parentW: d.querySelector('table').parentElement.clientWidth,
    };
  });
  console.log('mobile-table:', JSON.stringify(mobileTable));
  await page.screenshot({ path: out + '/shot-4-mobile.png' });

  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });

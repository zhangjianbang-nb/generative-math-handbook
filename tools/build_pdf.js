const puppeteer = require('/home/whu/workspace/servers/chatgpt-browser/node_modules/puppeteer-core');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const FORCE = process.argv.includes('--force');
const base = '/home/whu/workspace/ai_workspace/generative-math-handbook-20261125/site/book/';
const out = '/home/whu/workspace/ai_workspace/generative-math-handbook-20261125/book/pdf/';
fs.mkdirSync(out, { recursive: true });

function pages(pdf) {
  const info = execFileSync('pdfinfo', [pdf]).toString();
  const m = info.match(/Pages:\s+(\d+)/);
  return m ? parseInt(m[1]) : 0;
}

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/snap/bin/chromium',
    headless: true,
    pipe: true,
    userDataDir: '/home/whu/tmp-cr-book-pdf',
    args: ['--no-sandbox', '--disable-gpu']
  });
  const page = await browser.newPage();
  page.setDefaultNavigationTimeout(180000);
  const files = [];

  await page.goto('file://' + base + 'cover.html', { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const cover = out + 'cover.pdf';
  await page.pdf({ path: cover, printBackground: true, preferCSSPageSize: true, timeout: 900000 });
  files.push(cover);
  console.log('cover pages', pages(cover));

  for (let i = 1; i <= 25; i++) {
    const p = out + `ch-${i}.pdf`;
    if (!FORCE && fs.existsSync(p) && pages(p) > 0) {
      files.push(p);
      console.log('ch-' + i + ' skip existing');
      continue;
    }
    await page.goto(`file://${base}ch-${i}.html`, { waitUntil: 'domcontentloaded', timeout: 180000 });
    await page.waitForFunction(() => document.querySelectorAll('.katex').length > 0, { timeout: 90000 }).catch(() => {});
    await page.evaluate(() => document.fonts.ready);
    await new Promise(r => setTimeout(r, 1200));
    await page.pdf({ path: p, printBackground: true, preferCSSPageSize: true, timeout: 900000 });
    files.push(p);
    console.log('ch-' + i + ' pages', pages(p));
  }

  const merged = out + '全书.pdf';
  execFileSync('pdfunite', [...files, merged]);
  const total = pages(merged);
  const txt = execFileSync('pdftotext', [merged, '-'], { maxBuffer: 200 * 1024 * 1024 }).toString();
  const checks = {
    totalPages: total,
    hasTitle: txt.includes('生成式数学手册'),
    hasCh1: txt.includes('线性代数'),
    hasCh25: txt.includes('随机微分方程'),
    chars: txt.replace(/\s/g, '').length
  };
  console.log('MERGED ' + JSON.stringify(checks));
  console.log('size MB ' + (fs.statSync(merged).size / 1048576).toFixed(1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });

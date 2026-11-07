import { Browser, sleep } from 'file:///C:/Users/Admin/.gemini/config/skills/design-taste-frontend/scripts/lib/cdp.mjs';
const url = process.argv[2] || 'http://127.0.0.1:8501/';
const w = Number(process.argv[3] || 768);
const browser = await Browser.launch();
const page = await browser.newPage({ width: w, height: 900 });
await page.goto(url, { waitUntil: 'networkidle' });
await sleep(2500);
const out = await page.eval(`(() => {
  const grid = document.querySelector('.grid');
  if (!grid) return { found: false };
  const cs = getComputedStyle(grid);
  const chain = [];
  let el = grid;
  while (el && chain.length < 5) { chain.push({ tag: el.tagName, cls: (el.className||'').toString().slice(0,70) }); el = el.parentElement; }
  return { found: true, cols: cs.gridTemplateColumns, parent: chain[1], chain,
    gridW: Math.round(grid.getBoundingClientRect().width),
    kids: [...grid.children].slice(0,6).map(c => { const r = c.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y), cls: (c.className||'').toString().slice(0,40) }; }) };
})()`);
console.log(JSON.stringify(out, null, 2));
await browser.close();

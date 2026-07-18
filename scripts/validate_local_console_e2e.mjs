// MEMORYCORE_CONSOLE_E2E — Steel-driven E2E sweep of the operator console.
// LOCAL-ONLY eval: requires a running Steel browser (CDP at STEEL_WS), the
// console served with --host reachable from Steel, puppeteer-core installed,
// and a disposable local memory whose id fragment is passed via
// DISPOSABLE_FRAGMENT (the Forget test deletes it). Exercises every control:
// theme, tooltips, charts, filters, drilldown, reveal+hash proof, pack
// export, mode switch, backend toggles, routing matrix, flush, verify-all,
// declare (+duplicate rejection), config history, forget. 25 checks.
import puppeteer from "puppeteer-core";

const STEEL = process.env.STEEL_WS || "ws://127.0.0.1:3000/";
const CONSOLE_URL = process.env.CONSOLE_URL || "http://host.docker.internal:8787/";
const SHOTS = process.env.SHOTS_DIR || ".";
const results = [];
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function test(name, fn) {
  try { const info = await fn(); results.push({ name, pass: true, info: info || "" }); }
  catch (e) { results.push({ name, pass: false, info: String(e.message || e).slice(0, 160) }); }
}

const browser = await puppeteer.connect({ browserWSEndpoint: STEEL, defaultViewport: { width: 1600, height: 1000 } });
const page = await browser.newPage();
page.setDefaultTimeout(20000);

const armToast = () => page.evaluate(() => { const t = document.getElementById("toast"); t.style.opacity = 0; t.textContent = ""; });
const toastText = async () => {
  await page.waitForFunction(() => {
    const t = document.getElementById("toast");
    return t.style.opacity === "1" && t.textContent.length > 0;
  });
  return page.$eval("#toast", el => el.textContent);
};
const resetFilters = async () => {
  for (const id of ["mf-text", "af-text"]) await setInput(id, "");
  for (const id of ["mf-state", "mf-backend", "mf-type", "af-op", "af-client", "af-backend"])
    await page.evaluate(i => { const el = document.getElementById(i); el.value = ""; el.dispatchEvent(new Event("change")); }, id);
  await sleep(300);
};
const setInput = (id, value) => page.evaluate(([i, v]) => {
  const el = document.getElementById(i); el.value = v; el.dispatchEvent(new Event("input"));
}, [id, value]);
const clickButtonByText = async (text) => {
  const handle = await page.evaluateHandle(t =>
    [...document.querySelectorAll("button")].find(b => b.textContent.trim().includes(t)), text);
  const el = handle.asElement(); if (!el) throw new Error(`button not found: ${text}`);
  await el.click();
};

// ---- load & ambient ----
await page.goto(CONSOLE_URL, { waitUntil: "domcontentloaded" });
await page.waitForSelector("#tiles .tile");
await sleep(1200);

await test("page loads live", async () => {
  const gen = await page.$eval("#gen", el => el.textContent);
  if (!gen.includes("live")) throw new Error(`not live: ${gen}`);
  return gen.trim();
});
await test("six stat tiles render", async () => {
  const n = await page.$$eval("#tiles .tile", els => els.length);
  if (n !== 6) throw new Error(`expected 6 tiles, got ${n}`);
});
await page.screenshot({ path: `${SHOTS}/e2e-01-initial.png` });

await test("theme toggle flips both ways", async () => {
  const initial = await page.evaluate(() => document.documentElement.dataset.theme || "unset");
  await page.click(".theme-toggle"); await sleep(200);
  const flipped = await page.evaluate(() => document.documentElement.dataset.theme);
  await page.click(".theme-toggle"); await sleep(200);
  const back = await page.evaluate(() => document.documentElement.dataset.theme);
  if (!flipped || flipped === back) throw new Error(`no flip: ${initial}->${flipped}->${back}`);
  return `${initial} -> ${flipped} -> ${back}`;
});
await test("help tooltip appears on tile hover", async () => {
  await page.hover("#tiles .tile");
  await page.waitForFunction(() => document.getElementById("tip").style.opacity === "1");
  const tip = await page.$eval("#tip", el => el.textContent);
  if (tip.length < 15) throw new Error("tooltip too short");
  await page.mouse.move(5, 5);
  return tip.slice(0, 50);
});
await test("stacked-bar segment tooltip", async () => {
  await page.hover("#stackbar .seg");
  await page.waitForFunction(() => document.getElementById("tip").style.opacity === "1");
  const tip = await page.$eval("#tip", el => el.textContent);
  if (!tip.includes("of")) throw new Error(`unexpected tip: ${tip}`);
  await page.mouse.move(5, 5);
});
await test("activity charts render with hover", async () => {
  await page.waitForSelector("#trend-mem svg");
  const bars = await page.$$("#trend-audit rect");
  if (bars.length === 0) throw new Error("no audit bars");
  await bars[0].hover();
  await page.waitForFunction(() => document.getElementById("tip").style.opacity === "1");
  await page.mouse.move(5, 5);
  return `${bars.length} bars`;
});

// ---- memory table: search, filters, drilldown ----
await test("memory search filters by id fragment", async () => {
  await resetFilters();
  await setInput("mf-text", process.env.DISPOSABLE_FRAGMENT || "disposable-id-not-set"); await sleep(400);
  const count = await page.$eval("#mf-count", el => el.textContent);
  const rows = await page.$$eval("#memtable tr.mem", els => els.length);
  if (rows !== 1) throw new Error(`expected 1 row, got ${rows} (${count})`);
  await resetFilters();
  return count + " (id/pointer scope; content search is the server fan-out, by design)";
});
await test("state filter works", async () => {
  await resetFilters();
  await page.select("#mf-state", "verified"); await sleep(300);
  const bad = await page.$$eval("#memtable tr.mem td:nth-child(5)", tds =>
    tds.filter(td => !td.textContent.includes("verified")).length);
  if (bad > 0) throw new Error(`${bad} non-verified rows shown`);
  await page.select("#mf-state", ""); await sleep(300);
});
await test("backend + type filters work", async () => {
  await resetFilters();
  await page.select("#mf-backend", "jsonl_store");
  await page.select("#mf-type", "local"); await sleep(300);
  const rows = await page.$$eval("#memtable tr.mem", els => els.length);
  if (rows < 1) throw new Error("filters emptied the table unexpectedly");
  await page.select("#mf-backend", ""); await page.select("#mf-type", ""); await sleep(300);
  return `${rows} local/jsonl rows`;
});
await test("row click opens receipt drilldown", async () => {
  await resetFilters();
  await page.click("#memtable tr.mem");
  await page.waitForSelector("tr.detail");
  const txt = await page.$eval("tr.detail", el => el.textContent);
  if (!txt.includes("Provenance pointer") || !txt.includes("Receipt")) throw new Error("drilldown incomplete");
});
await test("reveal shows content with live hash proof", async () => {
  await clickButtonByText("Reveal content");
  await page.waitForSelector(".revealpane .hashcmp");
  const verdict = await page.$eval(".revealpane .hashcmp", el => el.textContent);
  if (!verdict.includes("hash verified live")) throw new Error(`verdict: ${verdict.slice(0, 60)}`);
  const content = await page.$eval(".revealpane pre.content", el => el.textContent);
  if (content.length < 20) throw new Error("content too short");
  return `content ${content.length} chars`;
});
await test("reveal persists across live re-render (EN-027 fix)", async () => {
  await sleep(6000); // beyond a poll cycle; content_access receipt forces re-render
  const still = await page.$(".revealpane .hashcmp");
  if (!still) throw new Error("reveal pane vanished after poll");
  const open = await page.$("tr.detail");
  if (!open) throw new Error("drilldown closed after poll");
});
await page.screenshot({ path: `${SHOTS}/e2e-02-reveal.png` });
await test("export evidence pack round-trips", async () => {
  await armToast();
  await clickButtonByText("Export evidence pack");
  const toast = await toastText();
  if (!toast.includes("integrity")) throw new Error(`toast: ${toast}`);
  return toast.slice(0, 60);
});
await test("row click again closes drilldown", async () => {
  await page.click("#memtable tr.mem"); await sleep(300);
  if (await page.$("tr.detail")) throw new Error("detail did not close");
});

// ---- audit explorer ----
await test("audit operation filter", async () => {
  await page.select("#af-op", "content_access"); await sleep(300);
  const rows = await page.$$eval("#audit .audit-row", els => els.length);
  const count = await page.$eval("#af-count", el => el.textContent);
  if (rows < 1) throw new Error("no content_access rows");
  await page.select("#af-op", ""); await sleep(300);
  return `${rows} rows (${count})`;
});
await test("audit client filter operator_ui", async () => {
  await page.select("#af-client", "operator_ui"); await sleep(300);
  const rows = await page.$$eval("#audit .audit-row", els => els.length);
  if (rows < 1) throw new Error("no operator_ui rows");
  await page.select("#af-client", ""); await sleep(300);
  return `${rows} operator_ui receipts`;
});
await test("audit text search", async () => {
  await setInput("af-text", "pack_export"); await sleep(300);
  const rows = await page.$$eval("#audit .audit-row", els => els.length);
  if (rows < 1) throw new Error("search found nothing");
  await setInput("af-text", ""); await sleep(300);
  return `${rows} matches`;
});

// ---- control plane ----
await test("mode switch to live-local and back", async () => {
  await armToast();
  await page.evaluate(() => [...document.querySelectorAll("#modeseg button")].find(b => b.textContent.includes("live-local")).click());
  const t1 = await toastText();
  if (!t1.includes("live-local")) throw new Error(`toast: ${t1}`);
  await sleep(1000);
  await armToast();
  await page.evaluate(() => [...document.querySelectorAll("#modeseg button")].find(b => b.textContent.trim() === "fixture").click());
  const t2 = await toastText();
  if (!t2.includes("fixture")) throw new Error(`toast: ${t2}`);
  return `${t1} | ${t2}`;
});
await test("backend toggle disable/enable (qmd)", async () => {
  const clickQmdToggle = () => page.evaluate(() => {
    const card = [...document.querySelectorAll(".bk-card")].find(c => c.textContent.includes("QMD"));
    card.querySelector(".toggle").click();
  });
  await armToast();
  await clickQmdToggle();
  const t1 = await toastText();
  if (!t1.includes("qmd disabled")) throw new Error(`toast: ${t1}`);
  await sleep(1000);
  await armToast();
  await clickQmdToggle();
  const t2 = await toastText();
  if (!t2.includes("qmd enabled")) throw new Error(`toast: ${t2}`);
});
await test("routing matrix mirror on/off", async () => {
  const clickCell = () => page.evaluate(() =>
    document.querySelector('.matrix input[data-t="local"][data-b="qmd"]').click());
  await armToast();
  await clickCell();
  const t1 = await toastText();
  if (!t1.includes("local ->")) throw new Error(`toast: ${t1}`);
  await sleep(1000);
  await armToast();
  await clickCell();
  const t2 = await toastText();
  if (!t2.includes("local -> jsonl_store")) throw new Error(`restore toast: ${t2}`);
  return `${t1} | ${t2}`;
});
await test("flush pending button", async () => {
  await armToast();
  await page.click("#btn-flush");
  const t = await toastText();
  if (!t.includes("flushed")) throw new Error(`toast: ${t}`);
  return t.slice(0, 50);
});
await test("re-verify all stamps button", async () => {
  await armToast();
  await page.click("#btn-verify");
  const t = await toastText();
  if (!t.includes("re-verified")) throw new Error(`toast: ${t}`);
  return t.slice(0, 70);
});
await test("declare backend form + duplicate rejection", async () => {
  await armToast();
  await page.evaluate(() => {
    document.getElementById("dec-id").value = "ui_probe";
    document.getElementById("dec-name").value = "UI Probe";
    document.getElementById("dec-class").value = "knowledge_brain";
    declareBackend();
  });
  const t1 = await toastText();
  if (!t1.includes("declared ui_probe")) throw new Error(`toast: ${t1}`);
  await sleep(1200);
  const card = await page.evaluate(() =>
    [...document.querySelectorAll(".bk-card")].some(c =>
      c.textContent.includes("UI Probe") && c.textContent.includes("no adapter installed")));
  if (!card) throw new Error("declared card not rendered as future");
  await armToast();
  await page.evaluate(() => { document.getElementById("dec-id").value = "ui_probe"; declareBackend(); });
  const t2 = await toastText();
  if (!t2.includes("already declared")) throw new Error(`dup toast: ${t2}`);
  return `${t1} | dup rejected`;
});
await test("config history records the session's actions", async () => {
  const txt = await page.$eval("#cfghistory", el => el.textContent);
  for (const action of ["backend_toggle", "routing_change", "mode_change", "declare_backend"]) {
    if (!txt.includes(action)) throw new Error(`missing ${action}`);
  }
});
await page.screenshot({ path: `${SHOTS}/e2e-03-controlplane.png` });

// ---- forget (on the disposable record only) ----
await test("forget removes the disposable record", async () => {
  await resetFilters();
  await setInput("mf-text", process.env.DISPOSABLE_FRAGMENT || "disposable-id-not-set"); await sleep(500);
  const rows = await page.$$eval("#memtable tr.mem", els => els.length);
  if (rows !== 1) throw new Error(`expected the disposable row, got ${rows}`);
  await page.click("#memtable tr.mem");
  await page.waitForSelector("tr.detail");
  await armToast();
  await clickButtonByText("Forget");
  const t = await toastText();
  if (!t.includes("forgot")) throw new Error(`toast: ${t}`);
  await sleep(1500);
  const after = await page.$$eval("#memtable tr.mem", els => els.length);
  if (after !== 0) throw new Error("record still visible after forget");
  await setInput("mf-text", "");
  return t.slice(0, 60);
});
await page.screenshot({ path: `${SHOTS}/e2e-04-final.png` });

await page.close();
browser.disconnect();

const passed = results.filter(r => r.pass).length;
console.log(JSON.stringify({ passed, failed: results.length - passed, total: results.length, results }, null, 1));
process.exit(results.length === passed ? 0 : 1);

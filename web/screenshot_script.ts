import { chromium } from "playwright";

const BASE = "http://localhost:3000";
const OUT = "public/screenshots";

const pages: { name: string; path: string; desc: string }[] = [
  { name: "home", path: "/", desc: "Home dashboard" },
  { name: "search", path: "/search", desc: "Search literature" },
  { name: "documents", path: "/documents", desc: "Documents list" },
  { name: "ask", path: "/ask", desc: "RAG Q&A" },
  { name: "ingest", path: "/ingest", desc: "Ingest pipeline" },
  { name: "editorial", path: "/editorial", desc: "Editorial view" },
  { name: "digest", path: "/digest", desc: "Daily digests" },
  { name: "discovery", path: "/discovery", desc: "Discovery feed" },
  { name: "settings", path: "/settings", desc: "System settings" },
];

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 2,
  });

  for (const p of pages) {
    const page = await context.newPage();
    await page.goto(`${BASE}${p.path}`, { waitUntil: "networkidle" });
    await page.screenshot({
      path: `${OUT}/${p.name}.png`,
      fullPage: p.name === "home" || p.name === "search" || p.name === "documents",
    });
    console.log(`[OK] ${p.name} -> ${p.desc}`);
    await page.close();
  }

  await browser.close();
  console.log("Done.");
})();
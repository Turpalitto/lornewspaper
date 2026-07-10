/**
 * Demo GIF capture script.
 * Captures the core user flow: Home -> Search -> Document Detail -> Q&A.
 * 
 * Requires: npx tsx demo_gif_script.ts
 * Output: public/screenshots/demo_search.gif (needs ffmpeg to convert frames to GIF)
 * 
 * For best results, run with backend providing real data at localhost:8000.
 * Without backend, captures UI structure with empty states.
 */

import { chromium } from "playwright";
import * as fs from "fs";
import * as path from "path";

const BASE = "http://localhost:3000";
const OUT_DIR = "public/screenshots/demo_frames";

// Core demo flow
const flow: { name: string; path: string; action?: string; delay?: number }[] = [
  { name: "01-home", path: "/", delay: 1500 },
  { name: "02-search", path: "/search", delay: 2000 },
  { name: "03-ask", path: "/ask", delay: 1500 },
  { name: "04-ingest", path: "/ingest", delay: 1500 },
  { name: "05-documents", path: "/documents", delay: 1500 },
  { name: "06-digest", path: "/digest", delay: 1500 },
];

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 2,
  });

  const page = await context.newPage();

  for (let i = 0; i < flow.length; i++) {
    const step = flow[i];
    await page.goto(`${BASE}${step.path}`, { waitUntil: "networkidle" });
    if (step.delay) await page.waitForTimeout(step.delay);
    await page.screenshot({
      path: path.join(OUT_DIR, `${step.name}.png`),
      fullPage: false,
    });
    console.log(`[${i + 1}/${flow.length}] ${step.name} -> ${step.path}`);
  }

  await browser.close();

  console.log(`\nFrames saved to ${OUT_DIR}/`);
  console.log("To create GIF with ffmpeg:");
  console.log(
    `  ffmpeg -framerate 0.5 -i ${OUT_DIR}/%02d-*.png -vf "fps=10,scale=1280:-1" public/screenshots/demo_flow.gif`
  );
  console.log("\nOr use online tool: https://ezgif.com/maker");
})();
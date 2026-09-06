import { chromium } from "playwright";
import { mkdir, writeFile, copyFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { spawn } from "node:child_process";

if (process.env.GITHUB_ACTIONS !== "true") {
  throw new Error("Run this capture job in GitHub Actions. It does not reconfigure the hosted review browser.");
}

const output = "review-results";
const base = "http://127.0.0.1:4180";
await mkdir(output, { recursive: true });
const server = spawn(process.execPath, ["review/serve.mjs", "site"], { stdio: "inherit" });
const captures = [];
const failures = [];
let browser;

try {
  let listening = false;
  for (let attempt = 0; attempt < 100; attempt++) {
    try { listening = (await fetch(base)).ok; } catch { /* Server is starting. */ }
    if (listening) break;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  if (!listening) throw new Error("The HTML test server did not start");
  browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
  });

  for (const viewport of [{ name: "desktop", width: 1440, height: 900 }, { name: "mobile", width: 430, height: 932 }]) {
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    // The software renderer only receives this repository's locally served build.
    await context.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.origin === base) return route.continue();
      if (["blob:", "data:"].includes(url.protocol)) return route.continue();
      return route.abort("blockedbyclient");
    });
    const page = await context.newPage();
    page.setDefaultTimeout(120_000);
    page.on("pageerror", (error) => failures.push(`${viewport.name}: ${error.message}`));
    page.on("console", (message) => {
      if (message.type() === "error") failures.push(`${viewport.name}: ${message.text()}`);
    });
    page.on("response", (response) => {
      if (response.status() >= 400) failures.push(`${viewport.name}: HTTP ${response.status()} ${response.url()}`);
    });
    try {
      await page.goto(base, { waitUntil: "domcontentloaded" });
      await page.getByRole("button", { name: "Pause simulation", exact: true }).click();
      await page.waitForFunction(() => Boolean(window.__EDEN_QA__), null, { timeout: 180_000 });
      await page.locator(".world-render-vitals").waitFor();

      const save = async (view, suffix = "") => {
        const frame = await page.evaluate((name) => {
          window.__EDEN_QA__.view(name);
          return window.__EDEN_QA__.frames;
        }, view);
        await page.waitForFunction((previous) => window.__EDEN_QA__.frames >= previous + 2, frame);
        const metrics = await page.evaluate(() => window.__EDEN_QA__.inspect());
        if (metrics.contextLost || metrics.humans !== 24 || metrics.triangles < 1000) {
          throw new Error(`Invalid rendered scene: ${JSON.stringify(metrics)}`);
        }
        const filename = `${viewport.name}-${view}${suffix}.png`;
        const buffer = await page.screenshot({ path: `${output}/${filename}`, timeout: 120_000 });
        const canvasFilename = `${viewport.name}-${view}${suffix}-scene.png`;
        const sceneImage = await page.evaluate(() => window.__EDEN_QA__.sceneImage());
        await writeFile(`${output}/${canvasFilename}`, Buffer.from(sceneImage.split(",")[1], "base64"));
        captures.push({ filename, canvasFilename, viewport, metrics, sha256: createHash("sha256").update(buffer).digest("hex") });
        console.log(`Captured ${filename}: ${metrics.renderer}`);
      };

      for (const view of viewport.name === "desktop" ? ["world", "camp", "east", "north"] : ["world", "camp"]) await save(view);

      if (viewport.name === "desktop") {
        for (const id of ["human-1", "human-2"]) {
          await page.evaluate((id) => window.__EDEN_QA__.pose({ id, clip: "idle", phase: 0.25 }), id);
          for (const view of ["human-front", "human-side", "human-rear"]) await save(view, `-${id}-idle`);
          for (const clip of ["walk", "run"]) for (const phase of [0.15, 0.5, 0.85]) {
            await page.evaluate((pose) => window.__EDEN_QA__.pose(pose), { id, clip, phase });
            await save("human-side", `-${id}-${clip}-${phase}`);
          }
        }
        await page.evaluate(() => window.__EDEN_QA__.pose(null));
      }
      const simulation = await page.evaluate(() => window.__EDEN_SIM_QA__.advance(90));
      await writeFile(`${output}/${viewport.name}-simulation-90s.json`, JSON.stringify(simulation, null, 2));
      await save("camp", "-after-90s");
    } catch (error) {
      failures.push(`${viewport.name}: ${error.stack || error}`);
      await page.screenshot({ path: `${output}/${viewport.name}-failure.png`, timeout: 30_000 }).catch(() => {});
    } finally {
      await context.close();
    }
  }
} catch (error) {
  failures.push(String(error.stack || error));
} finally {
  await browser?.close();
  server.kill("SIGTERM");
  await copyFile("asset-manifest.json", `${output}/asset-manifest.json`);
  await writeFile(`${output}/manifest.json`, JSON.stringify({
    gitCommit: process.env.GITHUB_SHA,
    runId: process.env.GITHUB_RUN_ID,
    createdAt: new Date().toISOString(),
    rendering: "CPU SwiftShader WebGL; visual evidence only, not a 4K/60fps benchmark",
    critic: { status: "awaiting independent review", score: null, requiredScoreExclusive: 8 },
    captures, failures,
  }, null, 2));
  await writeFile(`${output}/index.html`, `<!doctype html><html lang="en"><meta charset="UTF-8"><meta name="viewport" content="width=device-width"><title>Eden-7 render review</title><style>body{margin:32px;background:#101519;color:#e9edf1;font:16px system-ui}article{margin:32px 0}img{max-width:100%;height:auto}p{max-width:70ch}</style><h1>Eden-7 render review</h1><p>Actual WebGL captures. Independent critic score pending. Software rendering does not establish hardware frame rate.</p>${captures.map((item) => `<article><h2>${item.filename}</h2><img src="${item.filename}" alt="${item.filename}"><p><a href="${item.canvasFilename}">Inspect scene without interface overlays</a></p></article>`).join("")}<p><a href="manifest.json">Capture metadata and errors</a></p></html>`);
}
if (failures.length) {
  console.error(failures.join("\n"));
  process.exitCode = 1;
}

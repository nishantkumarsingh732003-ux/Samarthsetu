/**
 * Does the signed-in surface actually hold a frame rate?
 *
 * Every raised surface in this app deepens its shadow and lifts a pixel on hover. The
 * obvious way to build that — `transition: box-shadow` — is also the reason hover states
 * drop frames: the shadow is rasterised again on every animation frame, over the whole
 * area of the element, on the main thread. On a card the size of the best-match panel
 * that is a repaint of a third of the viewport, sixty times a second, on a phone whose
 * GPU is not going to help.
 *
 * `.lift` in `styles/globals.css` paints the shadow once into a pseudo-element and
 * animates only its `opacity`; the lift itself is a `transform`. Both are properties a
 * compositor can move without touching layout or paint. This script is what makes that
 * claim checkable rather than folklore.
 *
 * It signs in as the seeded demo citizen, then samples `requestAnimationFrame` deltas
 * across three things the dashboard actually does — scrolling, hovering every card and
 * button in turn, opening and closing the notification popover — and fails if any of
 * them drops frames, or if `box-shadow` turns up in any element's `transition-property`.
 *
 * rAF deltas rather than a devtools trace on purpose: a frame that took 34ms is a frame
 * the citizen saw twice, and that is the number worth defending.
 *
 *   node scripts/measure-frames.mjs                    # against localhost:3000
 *   node scripts/measure-frames.mjs --cpu 4            # as a mid-range Android
 *   node scripts/measure-frames.mjs --url http://…     # somewhere else
 *
 * Skips cleanly when the web app is not running, so it can sit in a check script without
 * failing a laptop with nothing up.
 */
import { existsSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const STORE = join(ROOT, "..", "..", "node_modules", ".pnpm");

/**
 * `chrome-launcher` and `puppeteer-core` arrive behind `lighthouse`, which is already a
 * devDependency here. pnpm does not hoist a transitive dependency, so they are resolved
 * out of the store by path rather than by name — this is a measuring tool, and it does
 * not get to add two packages to an app with a 200KB budget on its front door.
 */
function fromStore(name) {
  if (!existsSync(STORE)) return null;
  const dir = readdirSync(STORE).find((entry) => entry.startsWith(`${name}@`));
  if (!dir) return null;
  const path = join(STORE, dir, "node_modules", name);
  return existsSync(path) ? path : null;
}

const launcherPath = fromStore("chrome-launcher");
const puppeteerPath = fromStore("puppeteer-core");
if (!launcherPath || !puppeteerPath) {
  console.log(
    "frame check — skipped: chrome-launcher / puppeteer-core are not installed.\n" +
      "They come in behind lighthouse; run `pnpm install` at the repo root.",
  );
  process.exit(0);
}

const { launch } = await import(
  pathToFileURL(join(launcherPath, "dist", "index.js")).href
);
const puppeteer = (
  await import(
    pathToFileURL(join(puppeteerPath, "lib", "esm", "puppeteer", "puppeteer-core.js")).href
  )
).default;

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? fallback : args[index + 1];
};

const BASE = flag("url", "http://localhost:3000");
const CPU_THROTTLE = Number(flag("cpu", "1"));
const EMAIL = "citizen@setu.gov.in";
const PASSWORD = "setu-demo-2026";

/** A frame slower than one and a half refreshes is one the citizen saw twice. */
const BUDGET_MS = 16.7;
const JANK_MS = BUDGET_MS * 1.5;
/** Some jank is the harness, not the page. This is the line that fails the check. */
const MAX_JANKY_PCT = 5;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function webIsUp() {
  // Generous, and deliberately so: in dev the first request to a route compiles it, and
  // a three-second probe reported "nothing is running" against a server that was simply
  // busy building the page it was asked for.
  for (const attempt of [0, 1, 2]) {
    try {
      const response = await fetch(BASE, { signal: AbortSignal.timeout(15000) });
      // Any answer at all means something is serving. `/` redirects to `/en`, and a
      // 500 from a broken page is still a running server — and still worth measuring.
      return response.status > 0;
    } catch {
      if (attempt < 2) await sleep(2000);
    }
  }
  return false;
}

if (!(await webIsUp())) {
  console.log(`frame check — skipped: nothing is serving ${BASE}. Start it with \`docker compose up\`.`);
  process.exit(0);
}

/** Runs for the life of the page; `__sampling` gates whether deltas are kept. */
const SAMPLER = `
window.__frames = [];
window.__sampling = false;
(function tick(last) {
  requestAnimationFrame((now) => {
    if (window.__sampling && last) window.__frames.push(now - last);
    tick(now);
  });
})(0);
`;

function summarise(label, deltas) {
  if (deltas.length === 0) return { label, frames: 0 };
  const sorted = [...deltas].sort((a, b) => a - b);
  const mean = deltas.reduce((a, b) => a + b, 0) / deltas.length;
  const janky = deltas.filter((delta) => delta > JANK_MS).length;
  return {
    label,
    frames: deltas.length,
    fps: +(1000 / mean).toFixed(1),
    meanMs: +mean.toFixed(2),
    p95Ms: +sorted[Math.floor(sorted.length * 0.95)].toFixed(2),
    worstMs: +sorted[sorted.length - 1].toFixed(2),
    jankyPct: +((janky / deltas.length) * 100).toFixed(1),
  };
}

async function measure(page, label, action) {
  await page.evaluate(() => {
    window.__frames = [];
    window.__sampling = true;
  });
  await action();
  const deltas = await page.evaluate(() => {
    window.__sampling = false;
    return window.__frames;
  });
  return summarise(label, deltas);
}

let failures = 0;
const fail = (message) => {
  console.error(`  ✗ ${message}`);
  failures += 1;
};

const chrome = await launch({
  chromeFlags: [
    "--headless=new",
    "--window-size=1600,1000",
    // Without this the renderer is pinned to the display's refresh and every frame looks
    // perfect. Unpinned, a frame that takes too long shows up as a long frame.
    "--disable-gpu-vsync",
    "--no-sandbox",
  ],
});

const browser = await puppeteer.connect({
  browserURL: `http://localhost:${chrome.port}`,
  defaultViewport: { width: 1600, height: 1000 },
});

try {
  const page = (await browser.pages())[0] ?? (await browser.newPage());
  await page.setViewport({ width: 1600, height: 1000 });

  if (CPU_THROTTLE > 1) {
    const client = await page.createCDPSession();
    await client.send("Emulation.setCPUThrottlingRate", { rate: CPU_THROTTLE });
  }

  console.log(
    `frame check — ${BASE}${CPU_THROTTLE > 1 ? `, CPU throttled ${CPU_THROTTLE}x` : ""}\n`,
  );

  await page.goto(`${BASE}/en/signin`, { waitUntil: "networkidle2", timeout: 60000 });
  await page.waitForSelector('input[type="email"]', { timeout: 30000 });
  await page.type('input[type="email"]', EMAIL);
  await page.type('input[type="password"]', PASSWORD);
  await Promise.all([
    page.waitForNavigation({ waitUntil: "networkidle2", timeout: 60000 }).catch(() => {}),
    page.click('button[type="submit"]'),
  ]);

  await page.goto(`${BASE}/en/dashboard`, { waitUntil: "networkidle2", timeout: 60000 });
  await page.waitForSelector("h1", { timeout: 30000 });
  // The dashboard makes three reads; measuring while they land measures the network.
  await sleep(2000);

  if (page.url().includes("/signin")) {
    console.log("  skipped: the demo login was refused. Run `make demo` first.");
    process.exit(0);
  }

  await page.evaluate(SAMPLER);

  const results = [];

  results.push(
    await measure(page, "scroll the dashboard", async () => {
      for (const step of [...Array(40).keys(), ...[...Array(40).keys()].reverse()]) {
        await page.evaluate((y) => window.scrollTo(0, y), step * 25);
        await sleep(16);
      }
    }),
  );

  const targets = await page.$$("a.panel-link, .panel, .btn, button, a[class*=btn]");
  results.push(
    await measure(page, `hover ${targets.length} cards and buttons`, async () => {
      for (const handle of targets) {
        const box = await handle.boundingBox();
        if (!box) continue;
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await sleep(45);
      }
      await page.mouse.move(5, 5);
      await sleep(120);
    }),
  );

  results.push(
    await measure(page, "open and close the bell", async () => {
      for (let index = 0; index < 4; index += 1) {
        const bell = await page.$('button[aria-haspopup="dialog"]');
        if (!bell) break;
        await bell.click();
        await sleep(320);
        await page.keyboard.press("Escape");
        await sleep(320);
      }
    }),
  );

  console.log(
    "  " +
      "interaction".padEnd(34) +
      "fps".padStart(7) +
      "mean".padStart(9) +
      "p95".padStart(9) +
      "worst".padStart(9) +
      "janky".padStart(8),
  );
  for (const result of results) {
    if (!result.frames) {
      fail(`${result.label}: no frames sampled`);
      continue;
    }
    const ok = result.jankyPct <= MAX_JANKY_PCT;
    if (!ok) {
      fail(
        `${result.label}: ${result.jankyPct}% of frames over ${JANK_MS.toFixed(1)}ms ` +
          `(worst ${result.worstMs}ms)`,
      );
    }
    console.log(
      `  ${ok ? "✓" : "✗"} ` +
        result.label.padEnd(32) +
        String(result.fps).padStart(7) +
        `${result.meanMs}ms`.padStart(9) +
        `${result.p95Ms}ms`.padStart(9) +
        `${result.worstMs}ms`.padStart(9) +
        `${result.jankyPct}%`.padStart(8),
    );
  }

  // The structural half of the check. Frame numbers on a fast laptop can hide a
  // paint-heavy transition; the property list cannot.
  //
  // Read together with the duration, and that pairing is the whole subtlety: the
  // *initial* value of `transition-property` is `all`, so every element that transitions
  // nothing at all still reports `all` — with a duration of 0s. Reading the property on
  // its own flags every static card on the page, which is exactly what the first version
  // of this check did. Only a property with time on it is animating.
  const animated = await page.evaluate(() => {
    const seen = new Set();
    for (const element of document.querySelectorAll("a.panel-link, .btn, button, .panel")) {
      const style = getComputedStyle(element);
      const properties = style.transitionProperty.split(",").map((entry) => entry.trim());
      const durations = style.transitionDuration.split(",").map((entry) => entry.trim());
      properties.forEach((name, index) => {
        // One duration can cover several properties; CSS repeats the shorter list.
        const duration = durations[index % durations.length] ?? "0s";
        const seconds = duration.endsWith("ms")
          ? parseFloat(duration) / 1000
          : parseFloat(duration);
        if (name && name !== "none" && seconds > 0) seen.add(name);
      });
    }
    return [...seen].sort();
  });

  console.log(`\n  animated on the element itself: ${animated.join(", ") || "(none)"}`);
  if (animated.includes("box-shadow") || animated.includes("all")) {
    fail(
      "a hover state animates box-shadow (or `all`) directly. That repaints the whole " +
        "element every frame — use the .lift class, which moves opacity on a pseudo-element.",
    );
  }

  console.log("");
  if (failures > 0) {
    console.error(`frame check FAILED with ${failures} problem(s).`);
    process.exitCode = 1;
  } else {
    console.log("frame check passed.");
  }
} finally {
  await browser.disconnect();
  await chrome.kill();
}

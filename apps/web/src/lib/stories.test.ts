/**
 * The landing page says three named people were routed to three named schemes. This
 * asserts that those three people are still the ones the seed script actually creates.
 *
 * `scripts/seed/demo.py` runs each persona through the real engine and refuses to finish
 * if the verdict changes, so pinning this file to that one means the front page cannot
 * quietly start describing a journey the product no longer produces.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { SCHEME_FACTS } from "./schemeFacts";
import { STORIES, WORKED_EXAMPLE, WORKED_EXAMPLE_INCOME } from "./stories";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "..");
const SEED = readFileSync(join(REPO, "scripts", "seed", "demo.py"), "utf8");

const FAMILY_OF: Record<string, string> = Object.fromEntries(
  SCHEME_FACTS.map((scheme) => [scheme.code, scheme.family]),
);

describe("landing stories mirror the demo seed", () => {
  for (const story of STORIES) {
    describe(story.name, () => {
      it("is a persona in the seed", () => {
        expect(SEED).toContain(`"name": "${story.name}"`);
        expect(SEED).toContain(`"district": "${story.district}"`);
        expect(SEED).toContain(`"state": "${story.state}"`);
      });

      it("shows the amount the seed asks for", () => {
        expect(SEED).toContain(`"amount": ${story.amount}`);
      });

      it("names a scheme the rule pack still has", () => {
        expect(FAMILY_OF[story.schemeCode]).toBeDefined();
      });

      it("routes to the family the seed asserts", () => {
        // The seed block for this persona, up to the next persona or the end of the list.
        const start = SEED.indexOf(`"name": "${story.name}"`);
        const block = SEED.slice(start, start + 1400);
        expect(block).toContain(`"expect_family": "${FAMILY_OF[story.schemeCode]}"`);
      });
    });
  }

  it("the worked example is the redirect persona — the one that carries the pitch", () => {
    const start = SEED.indexOf(`"name": "${WORKED_EXAMPLE.name}"`);
    const block = SEED.slice(start, start + 1400);
    expect(block).toContain('"expect_redirect_from": "NSFDC_MICRO_FINANCE"');
    expect(block).toContain(`"annual_family_income": ${WORKED_EXAMPLE_INCOME}`);
  });

  it("keeps its income under the Rs 5,00,000 ceiling the problem statement fixes", () => {
    expect(WORKED_EXAMPLE_INCOME).toBeLessThanOrEqual(500000);
  });

  it("credits every photograph", () => {
    for (const { photo } of STORIES) {
      expect(photo.url.startsWith("https://upload.wikimedia.org/")).toBe(true);
      expect(photo.author).not.toBe("");
      expect(photo.license).not.toBe("");
      expect(photo.pageUrl.startsWith("https://commons.wikimedia.org/")).toBe(true);
    }
  });
});

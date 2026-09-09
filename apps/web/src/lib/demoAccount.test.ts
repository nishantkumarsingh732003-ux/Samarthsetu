/**
 * The sign-in page names the demo account. This is what stops that name drifting away
 * from the account the API actually creates when the button is pressed.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { DEMO_ACCOUNT } from "./demoAccount";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "..");
const SERVICE = readFileSync(
  join(REPO, "apps", "api", "app", "services", "citizen_accounts.py"),
  "utf8",
);

describe("demoAccount mirrors the API's demo persona", () => {
  it("names the citizen DEMO_CITIZEN creates", () => {
    expect(SERVICE).toContain(`"display_name": "${DEMO_ACCOUNT.name}"`);
  });

  it("names the district DEMO_CITIZEN creates", () => {
    expect(SERVICE).toContain(`"district": "${DEMO_ACCOUNT.district}"`);
  });

  it("names the category DEMO_PROFILE creates", () => {
    expect(SERVICE).toContain(`"category": "${DEMO_ACCOUNT.category}"`);
  });

  it("describes a tailoring unit, which the caption calls it", () => {
    expect(SERVICE).toContain('"occupation_type": "Tailor"');
    expect(SERVICE).toContain("Tailoring Unit");
  });

  it("keeps the persona inside the Rs 5,00,000 income ceiling", () => {
    const income = SERVICE.match(/"annual_family_income":\s*(\d+)/);
    expect(income).not.toBeNull();
    expect(Number(income?.[1])).toBeLessThanOrEqual(500000);
  });
});

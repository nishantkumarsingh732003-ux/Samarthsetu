import { describe, expect, it } from "vitest";

import { formatDistance, formatRupees } from "./format";

describe("formatRupees", () => {
  it("groups in lakhs, not thousands", () => {
    // 12,00,000 and not 1,200,000. A citizen reads lakhs, and a figure grouped the
    // Western way is misread at a glance — which for an amount of money is not cosmetic.
    expect(formatRupees(1200000, "en")).toBe("12,00,000");
    expect(formatRupees(140000, "en")).toBe("1,40,000");
  });

  it("rounds rather than showing paise", () => {
    expect(formatRupees(1250.6, "en")).toBe("1,251");
  });

  it("keeps Indian grouping in every supported locale", () => {
    for (const locale of ["en", "hi", "mr", "bn", "ta", "te"]) {
      // The digits themselves may be localised; the grouping must not become Western.
      const formatted = formatRupees(1200000, locale);
      expect(formatted.split(/[.,]/).at(-1)).toHaveLength(3);
      expect(formatted).not.toMatch(/^\d,\d{3},\d{3}$/);
    }
  });
});

describe("formatDistance", () => {
  it("keeps one decimal when close and rounds when far", () => {
    expect(formatDistance(2.34)).toBe("2.3");
    expect(formatDistance(24.6)).toBe("25");
  });

  it("shows a dash rather than 0 when the distance is unknown", () => {
    // A partner with no geometry is at an unknown distance, not at zero distance.
    expect(formatDistance(null)).toBe("—");
  });
});

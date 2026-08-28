import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Large tap targets and high contrast: users may be low-literacy, on low-end phones.
      fontSize: { base: "1.0625rem" },
    },
  },
  plugins: [],
} satisfies Config;

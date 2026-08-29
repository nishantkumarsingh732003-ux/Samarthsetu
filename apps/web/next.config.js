const createNextIntlPlugin = require("next-intl/plugin");

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The citizen route has a hard JS budget (CLAUDE.md: 2G, a Rs 6,000 phone), so the
  // build fails loudly rather than quietly shipping a heavier bundle.
  productionBrowserSourceMaps: false,
};

module.exports = withNextIntl(nextConfig);

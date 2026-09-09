const createNextIntlPlugin = require("next-intl/plugin");

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The citizen route has a hard JS budget (CLAUDE.md: 2G, a Rs 6,000 phone), so the
  // build fails loudly rather than quietly shipping a heavier bundle.
  productionBrowserSourceMaps: false,
  images: {
    // The landing page's story photographs. Wikimedia Commons, CC BY-SA 4.0, credited
    // under the carousel — and the ONLY remote host this app will load an image from.
    // Next resizes and re-encodes them on the way through, which is the whole reason
    // they are allowed at all: the originals are 200-450KB of JPEG each and the citizen
    // route is budgeted for 2G. See src/lib/stories.ts.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "upload.wikimedia.org",
        pathname: "/wikipedia/commons/**",
      },
    ],
    // A year. These files are content-addressed by Wikimedia and never change in place.
    minimumCacheTTL: 31536000,
  },
};

module.exports = withNextIntl(nextConfig);

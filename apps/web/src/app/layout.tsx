import type { Metadata, Viewport } from "next";

import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "SETU",
  description:
    "Find the government credit scheme that fits you, and the nearest Channel Partner authorised to process it.",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // Never lock zoom: a low-vision citizen must be able to enlarge the page.
  maximumScale: 5,
  themeColor: "#0E4266",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return children;
}

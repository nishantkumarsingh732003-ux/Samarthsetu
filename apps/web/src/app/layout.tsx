import type { Metadata, Viewport } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "SETU — Scheme Eligibility & Transparent Uptake",
  description:
    "Find the government credit scheme that fits you, and the nearest Channel Partner authorised to process it.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // The citizen route must stay readable when a low-vision user zooms.
  maximumScale: 5,
  themeColor: "#0b3b5c",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  );
}

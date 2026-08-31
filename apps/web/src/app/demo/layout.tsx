/**
 * Pitch-tool shell, outside the localised citizen tree.
 *
 * `/demo` is for showing the architecture to a reviewer, not for serving a citizen, so
 * it carries no locale routing, no offline shell, and no service worker — nothing here
 * should be cached onto a citizen's phone.
 */
export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-canvas antialiased">{children}</body>
    </html>
  );
}

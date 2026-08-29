"use client";

import { useEffect } from "react";

/**
 * Registers the offline shell. Deliberately tiny and hand-written rather than pulling
 * in a PWA plugin: the whole point of this route is a small bundle.
 */
export function ServiceWorker() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // An unregistered worker only costs offline support, never the page itself.
    });
  }, []);
  return null;
}

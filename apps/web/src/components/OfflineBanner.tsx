"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

/**
 * "Offline — showing saved results".
 *
 * Persistent rather than a toast: on a 2G connection the citizen needs to know for the
 * whole session why the page is not changing, not for three seconds.
 */
export function OfflineBanner() {
  const t = useTranslations("common");
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  if (!offline) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="bg-warn-bg px-4 py-3 text-center text-base font-medium text-warn-fg"
    >
      {t("offline")}
    </div>
  );
}

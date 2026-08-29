import { NextIntlClientProvider } from "next-intl";
import { getMessages, unstable_setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { OfflineBanner } from "@/components/OfflineBanner";
import { ServiceWorker } from "@/components/ServiceWorker";
import { LOCALES, isLocale, type Locale } from "@/i18n/config";

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!isLocale(locale)) notFound();
  unstable_setRequestLocale(locale as Locale);

  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body className="min-h-screen antialiased">
        <NextIntlClientProvider messages={messages}>
          <OfflineBanner />
          {children}
          <ServiceWorker />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}

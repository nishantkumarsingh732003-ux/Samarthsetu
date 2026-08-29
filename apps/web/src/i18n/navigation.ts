import { createSharedPathnamesNavigation } from "next-intl/navigation";

import { LOCALES } from "./config";

export const { Link, redirect, usePathname, useRouter } =
  createSharedPathnamesNavigation({ locales: LOCALES });

/**
 * `cn` — the class merger every shadcn component expects.
 *
 * `clsx` resolves conditionals and arrays; `twMerge` then drops Tailwind classes that a
 * later one overrides, so a caller passing `className="px-8"` beats the variant's `px-5`
 * instead of losing to whichever CSS rule happens to come last in the stylesheet.
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

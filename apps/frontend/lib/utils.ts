import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function cleanCardId(rawId: string) {
  const safeDecoded = (() => {
    try {
      return decodeURIComponent(rawId);
    } catch {
      return rawId;
    }
  })();

  const trimmed = safeDecoded.trim();
  const uuidMatch = trimmed.match(
    /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/,
  );
  if (uuidMatch) {
    return uuidMatch[0].toLowerCase();
  }

  return trimmed.replace(/["']/g, "").replace(/\s+/g, "");
}

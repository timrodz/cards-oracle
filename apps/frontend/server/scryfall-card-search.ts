"use server";

import { ScryfallCardApiResponse } from "@/lib/types/scryfall";

// Docs: https://scryfall.com/docs/api/cards/search
const API_ENDPOINT = "https://api.scryfall.com/cards/search";

async function fetchScryfallPage(
  url: string,
): Promise<ScryfallCardApiResponse> {
  const response = await fetch(url);
  console.debug("ScryfallApiSearchCards", response.status);
  if (!response.ok) {
    throw new Error(`Scryfall API error: ${response.status}`);
  }
  // TODO: Have to cleanup the response for set names so it's case insensitive
  return (await response.json()) as ScryfallCardApiResponse;
}

/**
 *
 * @param query Card to search for
 * @returns
 */
export async function ScryfallApiSearchCards(
  query: string,
): Promise<ScryfallCardApiResponse | null> {
  // Produces "q=<query>"
  const queryParameters = new URLSearchParams({
    order: "cmc",
    q: query,
  }).toString();
  try {
    // TODO: Parse with Zod
    return await fetchScryfallPage(`${API_ENDPOINT}?${queryParameters}`);
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function ScryfallApiSearchCardsNextPage(
  nextPageUrl: string,
): Promise<ScryfallCardApiResponse | null> {
  try {
    // TODO: Parse with Zod
    return await fetchScryfallPage(nextPageUrl);
  } catch (err) {
    console.error(err);
    return null;
  }
}

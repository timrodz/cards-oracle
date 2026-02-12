import { mapColorIdentity } from "@/lib/elevenlabs";
import {
  ElevenlabsToolScryfallCardFiltererParams,
  ElevenlabsToolScryfallCardSearchParams,
} from "@/lib/types/elevenlabs";
import {
  ScryfallCard,
  ScryfallCardApiResponse,
  ScryfallCardColor,
} from "@/lib/types/scryfall";
import {
  ScryfallApiSearchCards,
  ScryfallApiSearchCardsNextPage,
} from "@/server/scryfall-card-search";
import { useMemo, useState } from "react";

interface ScryfallCardsProps {
  initialData?: ScryfallCardApiResponse;
}
export function useScryfallCards({ initialData }: ScryfallCardsProps) {
  const [allCards, setAllCards] = useState<ScryfallCard[]>(
    initialData?.data ?? [],
  );
  const [hasMoreCards, setHasMoreCards] = useState<boolean>(
    initialData?.has_more ?? false,
  );
  const [nextPageUrl, setNextPageUrl] = useState<string | null>(
    initialData?.next_page ?? null,
  );
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Filters
  const [selectedCmc, setSelectedCmc] = useState<number | null>(null);
  const [selectedColors, setSelectedColors] = useState<ScryfallCardColor[]>([]);
  const [selectedSetName, setSelectedSetName] = useState<string | null>(null);

  const cmcOptions = useMemo(() => {
    const unique = new Set<number>(allCards.map((c) => c.cmc));
    return Array.from(unique).sort((a, b) => a - b);
  }, [allCards]);

  const colorOptions = useMemo(() => {
    const unique = new Set<ScryfallCardColor>();
    allCards
      .map((c) => c.color_identity)
      .forEach((card) => {
        if (!card.length) {
          unique.add(null);
          return;
        }
        card.forEach((color) => unique.add(color));
      });
    return Array.from(unique).sort();
  }, [allCards]);

  const setNameOptions = useMemo(() => {
    const unique = new Set<string>(allCards.map((c) => c.set_name));
    return Array.from(unique).sort();
  }, [allCards]);

  const filteredCards = useMemo(
    () =>
      allCards.filter((card) => {
        if (selectedCmc && card.cmc !== Number(selectedCmc)) {
          return false;
        }
        if (selectedColors.length > 0) {
          if (selectedColors.includes(null)) {
            return (
              selectedColors.length === 1 && card.color_identity.length === 0
            );
          }
          const matchesAllColors = selectedColors.every((color) =>
            card.color_identity.includes(color),
          );
          if (!matchesAllColors) {
            return false;
          }
        }
        if (selectedSetName && card.set_name !== selectedSetName) {
          return false;
        }
        return true;
      }),
    [allCards, selectedCmc, selectedColors, selectedSetName],
  );

  const clearFilters = () => {
    setSelectedCmc(null);
    setSelectedColors([]);
    setSelectedSetName(null);
  };

  const onHandleScryfallCardSearch = async (
    params: ElevenlabsToolScryfallCardSearchParams,
  ): Promise<string> => {
    const { query } = params;
    console.debug("scryfall card search", query);
    const response = await ScryfallApiSearchCards(query);
    console.log("scryfall card search response", {
      response: response,
    });
    const resultCount = response?.data.length ?? 0;
    if (!response || !resultCount) {
      console.warn("scryfall card search - No results");
      setAllCards([]);
      setHasMoreCards(false);
      setNextPageUrl(null);
      clearFilters();
      return `You searched for ${query} but found no results`;
    }

    setAllCards(response.data);
    setHasMoreCards(Boolean(response.has_more));
    setNextPageUrl(response.next_page ?? null);
    clearFilters();
    return `I found ${resultCount} results. Please click on them to learn more! Talk soon.`;
  };

  const onHandleScryfallCardFilterer = async (
    params: ElevenlabsToolScryfallCardFiltererParams,
  ) => {
    const {
      filters: { mana_cost, color_identity, set_name },
    } = params;
    console.debug("card filter", { mana_cost, color_identity, set_name });
    // For every field provided, modify the filters with the information.
    if (mana_cost) {
      setSelectedCmc(mana_cost);
    }
    if (color_identity) {
      setSelectedColors(mapColorIdentity(color_identity));
    }
    if (set_name) {
      setSelectedSetName(set_name);
    }
    // TODO: Fill out response
    return `My response has indicated ${allCards.length}`;
  };

  const loadMoreCards = async () => {
    if (!nextPageUrl || isLoadingMore) return;
    setIsLoadingMore(true);
    const response = await ScryfallApiSearchCardsNextPage(nextPageUrl);
    if (!response) {
      setIsLoadingMore(false);
      return;
    }

    setAllCards((prev) => [...prev, ...response.data]);
    setHasMoreCards(Boolean(response.has_more));
    setNextPageUrl(response.next_page ?? null);
    setIsLoadingMore(false);
  };

  return {
    data: {
      allCards,
      cmcOptions,
      colorOptions,
      setNameOptions,
      filteredCards,
      hasMoreCards,
      isLoadingMore,
      selectedCmc,
      selectedColors,
      selectedSetName,
    },
    operations: {
      loadMoreCards,
      onHandleScryfallCardSearch,
      onHandleScryfallCardFilterer,
      setSelectedCmc,
      setSelectedColors,
      setSelectedSetName,
    },
  };
}

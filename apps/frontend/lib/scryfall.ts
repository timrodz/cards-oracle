import { CardFilters } from "./types/filters";
import { ScryfallCard, ScryfallCardColor } from "./types/scryfall";

export function filterCards(
  allCards: ScryfallCard[],
  filters: CardFilters,
): ScryfallCard[] {
  const { cmc, colors, setName } = filters;
  return allCards.filter((card) => {
    if (cmc && card.cmc !== Number(cmc)) {
      return false;
    }
    if (colors && colors.length > 0) {
      if (colors.includes(null)) {
        return colors.length === 1 && card.color_identity.length === 0;
      }
      const matchesAllColors = colors.every((color) =>
        card.color_identity.includes(color),
      );
      if (!matchesAllColors) {
        return false;
      }
    }
    if (setName && card.set_name !== setName) {
      return false;
    }
    return true;
  });
}

export function scryfallColorToLabel(color: ScryfallCardColor): string {
  switch (color) {
    case "B":
      return "Black";
    case "W":
      return "White";
    case "R":
      return "Red";
    case "G":
      return "Green";
    case "U":
      return "Blue";
    case null:
      return "Colorless";
  }
}

import { ScryfallCardColor } from "./scryfall";

export interface CardFilters {
  cmc?: number;
  colors?: ScryfallCardColor[];
  setName?: string;
}

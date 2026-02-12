/**
 * Source: https://scryfall.com/docs/api/cards
 */

export interface ScryfallCard {
  object: "card";
  _id: string;
  id: string;
  oracle_id: string;
  multiverse_ids: number[];
  resource_id?: string;
  mtgo_id?: number;
  mtgo_foil_id?: number;
  arena_id?: number;
  tcgplayer_id?: number;
  cardmarket_id?: number;
  name: string;
  lang: string;
  released_at: string;
  uri: string;
  scryfall_uri: string;
  layout: string;
  highres_image: boolean;
  image_status: string;
  image_uris: {
    small: string;
    normal: string;
    large: string;
    png: string;
    art_crop: string;
    border_crop: string;
  } | null;
  card_faces?: ScryfallCardFace[];
  mana_cost: string;
  cmc: number;
  type_line: string;
  oracle_text: string;
  power?: string;
  toughness?: string;
  colors: ScryfallCardColor[];
  color_identity: ScryfallCardColor[];
  keywords: string[];
  produced_mana?: string[];
  legalities: ScryfallCardLegalities;
  games: string[];
  reserved: boolean;
  game_changer: boolean;
  foil: boolean;
  nonfoil: boolean;
  finishes: string[];
  oversized: boolean;
  promo: boolean;
  reprint: boolean;
  variation: boolean;
  set_id: string;
  set: string;
  set_name: string;
  set_type: string;
  set_uri: string;
  set_search_uri: string;
  scryfall_set_uri: string;
  rulings_uri: string;
  prints_search_uri: string;
  collector_number: string;
  digital: boolean;
  rarity: string;
  flavor_text?: string;
  card_back_id: string;
  artist: string;
  artist_ids: string[];
  illustration_id: string;
  border_color: string;
  frame: string;
  frame_effects?: string[];
  full_art: boolean;
  textless: boolean;
  booster: boolean;
  story_spotlight: boolean;
  edhrec_rank?: number;
  penny_rank?: number;
  prices: ScryfallCardPrices;
  related_uris: ScryfallCardRelatedUris;
  purchase_uris: ScryfallCardPurchaseUris;
}

export interface MongoDBScryfallCard extends ScryfallCard {
  _id: string;
}

export interface ScryfallCardLegalities {
  [format: string]: "legal" | "not_legal" | "restricted" | "banned";
}

export interface ScryfallCardFace {
  name: string;
  mana_cost: number;
  type_line: string;
  oracle_text?: string;
  colors: ScryfallCardColor;
  image_uris?: {
    small: string;
    normal: string;
    large: string;
    png: string;
    art_crop: string;
    border_crop: string;
  };
}

export interface ScryfallCardPrices {
  usd: string | null;
  usd_foil: string | null;
  usd_etched: string | null;
  eur: string | null;
  eur_foil: string | null;
  tix: string | null;
}

export interface ScryfallCardRelatedUris {
  gatherer?: string;
  tcgplayer_infinite_articles?: string;
  tcgplayer_infinite_decks?: string;
  edhrec?: string;
  [key: string]: string | undefined;
}

export interface ScryfallCardPurchaseUris {
  tcgplayer?: string;
  cardmarket?: string;
  cardhoarder?: string;
  [key: string]: string | undefined;
}

export type ScryfallCardColor = "W" | "R" | "B" | "U" | "G" | null;

export interface ScryfallCardApiResponse {
  object: "list";
  total_cards: number;
  has_more: boolean;
  next_page?: string;
  data: ScryfallCard[];
}

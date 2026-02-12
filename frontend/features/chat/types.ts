import { MongoDBScryfallCard } from "@/lib/types/scryfall";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  cards?: MongoDBScryfallCard[];
  isSeekingCard?: boolean;
  seekingLabel?: string;
};

export type StreamEventType =
  | "meta"
  | "chunk"
  | "done"
  | "seeking_card"
  | "found_card";

export type StreamEvent = {
  type?: StreamEventType;
  content?: string;
  id?: string;
};

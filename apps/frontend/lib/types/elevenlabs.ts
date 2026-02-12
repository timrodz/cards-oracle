/**
 * These parameters come from Elevenlabs client tool definitions
 */

export interface ElevenlabsToolScryfallCardSearchParams {
  query: string;
}

type ColorIdentiy = "red" | "white" | "black" | "green" | "colorless" | "blue";

export interface ElevenlabsToolScryfallCardFiltererParams {
  filters: {
    mana_cost?: number;
    color_identity?: ColorIdentiy[];
    set_name?: string;
  };
}

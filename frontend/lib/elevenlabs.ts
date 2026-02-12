import { ScryfallCardColor } from "./types/scryfall";

export function mapColorIdentity(colors: string[]): ScryfallCardColor[] {
  return colors
    .map((color) => {
      switch (color) {
        case "white":
          return "W";
        case "blue":
          return "U";
        case "black":
          return "B";
        case "red":
          return "R";
        case "green":
          return "G";
        case "colorless":
          return null;
        default:
          console.error(
            `Uknown color parameter from Elevenlabs response ${color}`,
          );
          break;
      }
    })
    .filter((c) => typeof c !== "undefined");
}

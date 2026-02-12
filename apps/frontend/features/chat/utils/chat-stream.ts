import { StreamEvent } from "@/features/chat/types";

export function parseSsePayloads(buffer: string) {
  const rawEvents = buffer.split(/\r?\n\r?\n/);
  const remainder = rawEvents.pop() ?? "";
  const payloads = rawEvents
    .map((rawEvent) =>
      rawEvent
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean),
    )
    .filter((lines) => lines.length > 0)
    .map((lines) =>
      lines
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.replace(/^data:\s?/, ""))
        .join("\n"),
    )
    .filter(Boolean);

  return {
    remainder,
    payloads,
  };
}

export function parseStreamEvent(payload: string): StreamEvent | null {
  try {
    return JSON.parse(payload) as StreamEvent;
  } catch {
    return null;
  }
}

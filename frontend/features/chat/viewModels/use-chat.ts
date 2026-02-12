"use client";

import { cleanCardId } from "@/lib/utils";
import { ScryfallCard } from "@/lib/types/scryfall";
import { useState } from "react";
import { ChatMessage } from "@/features/chat/types";
import {
  parseSsePayloads,
  parseStreamEvent,
} from "@/features/chat/utils/chat-stream";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://localhost:8000";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const appendToAssistant = (text: string) => {
    if (!text) {
      return;
    }
    setMessages((prev) => {
      if (prev.length === 0) {
        return prev;
      }
      const next = [...prev];
      const last = next[next.length - 1];
      if (last?.role !== "assistant") {
        return prev;
      }
      next[next.length - 1] = {
        ...last,
        content: `${last.content}${text}`,
      };
      return next;
    });
  };

  const appendAssistantNotice = (text: string) => {
    setMessages((prev) => {
      if (!text || prev.length === 0) {
        return prev;
      }
      const next = [...prev];
      const last = next[next.length - 1];
      if (last?.role !== "assistant") {
        return prev;
      }
      const separator = last.content.length > 0 ? "\n" : "";
      next[next.length - 1] = {
        ...last,
        content: `${last.content}${separator}${text}\n`,
      };
      return next;
    });
  };

  const appendCardToAssistant = (card: ScryfallCard) => {
    setMessages((prev) => {
      if (prev.length === 0) {
        return prev;
      }
      const next = [...prev];
      const last = next[next.length - 1];
      if (last?.role !== "assistant") {
        return prev;
      }
      const existingCards = last.cards ?? [];
      if (existingCards.some((existingCard) => existingCard.id === card.id)) {
        return prev;
      }
      next[next.length - 1] = {
        ...last,
        cards: [...existingCards, card],
        isSeekingCard: false,
        seekingLabel: undefined,
      };
      return next;
    });
  };

  const setSeekingCardState = (isSeekingCard: boolean, label?: string) => {
    setMessages((prev) => {
      if (prev.length === 0) {
        return prev;
      }
      const next = [...prev];
      const last = next[next.length - 1];
      if (last?.role !== "assistant") {
        return prev;
      }
      next[next.length - 1] = {
        ...last,
        isSeekingCard,
        seekingLabel: isSeekingCard ? label : undefined,
      };
      return next;
    });
  };

  const fetchCardById = async (id: string) => {
    const response = await fetch(
      `${API_BASE}/cards/${encodeURIComponent(id)}`,
      {
        method: "GET",
      },
    );
    if (!response.ok) {
      throw new Error(`Card lookup failed with ${response.status}`);
    }
    return (await response.json()) as ScryfallCard;
  };

  const sendMessage = async (rawQuery: string) => {
    const query = rawQuery.trim();
    if (!query || isStreaming) {
      return;
    }

    setInput("");
    setError(null);
    setIsStreaming(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: query },
      { role: "assistant", content: "" },
    ]);

    try {
      const response = await fetch(
        `${API_BASE}/search/stream?query=${encodeURIComponent(query)}`,
        {
          method: "GET",
        },
      );

      if (!response.ok) {
        throw new Error(`Request failed with ${response.status}`);
      }
      if (!response.body) {
        throw new Error("Response body is empty");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let doneEventSeen = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });

        const { remainder, payloads } = parseSsePayloads(buffer);
        buffer = remainder;

        for (const payload of payloads) {
          if (!payload || payload === "[DONE]") {
            continue;
          }

          const parsed = parseStreamEvent(payload);
          if (!parsed) {
            appendToAssistant(payload);
            continue;
          }

          if (parsed.type === "chunk" && typeof parsed.content === "string") {
            appendToAssistant(parsed.content);
            continue;
          }

          if (parsed.type === "seeking_card") {
            setSeekingCardState(
              true,
              parsed.content?.trim() || "Searching for card details",
            );
            continue;
          }

          if (parsed.type === "found_card" && parsed.id) {
            setSeekingCardState(false);
            try {
              const normalizedId = cleanCardId(parsed.id);
              if (!normalizedId) {
                appendAssistantNotice("Card lookup skipped: invalid card id.");
                continue;
              }
              const card = await fetchCardById(normalizedId);
              appendCardToAssistant(card);
            } catch (cardError) {
              const cardMessage =
                cardError instanceof Error
                  ? cardError.message
                  : "Failed to load card details";
              appendAssistantNotice(cardMessage);
            }
            continue;
          }

          if (parsed.type === "done") {
            setSeekingCardState(false);
            doneEventSeen = true;
            break;
          }
        }

        if (doneEventSeen) {
          break;
        }
      }

      if (!doneEventSeen && buffer.trim()) {
        const parsedBuffer = parseStreamEvent(buffer.trim());
        if (parsedBuffer?.type === "chunk" && parsedBuffer.content) {
          appendToAssistant(parsedBuffer.content);
        } else if (!parsedBuffer) {
          appendToAssistant(buffer);
        }
      }

      if (!doneEventSeen) {
        setError("Stream ended before a done event was received.");
      }
    } catch (streamError) {
      const message =
        streamError instanceof Error ? streamError.message : "Unknown error";
      setError(message);
    } finally {
      setSeekingCardState(false);
      setIsStreaming(false);
    }
  };

  return {
    data: {
      apiBase: API_BASE,
      messages,
      input,
      isStreaming,
      error,
    },
    operations: {
      setInput,
      sendMessage,
    },
  };
}

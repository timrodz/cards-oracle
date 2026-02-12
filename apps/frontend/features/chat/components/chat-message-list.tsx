"use client";

import { useEffect, useRef } from "react";
import { Card } from "@/components/ui/card";
import { ScryfallCardOverview } from "@/features/scryfall-card-search/components/scryfall-card";
import { ChatMessage } from "@/features/chat/types";

interface ChatMessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export function ChatMessageList({
  messages,
  isStreaming,
}: ChatMessageListProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: isStreaming ? "auto" : "smooth",
      block: "end",
    });
  }, [isStreaming, messages]);

  return (
    <Card className="p-4 min-h-50">
      {messages.length === 0 ? (
        <div className="text-muted-foreground">
          Start the conversation with a card question or deck idea.
        </div>
      ) : (
        <div className="flex flex-1 flex-col gap-4 overflow-y-auto">
          {messages.map((message, index) => (
            <Card
              key={`${message.role}-${index}`}
              className={`w-full rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                message.role === "user"
                  ? "ml-auto max-w-[80%] bg-primary text-primary-foreground"
                  : "mr-auto max-w-[85%] bg-muted text-foreground"
              }`}
            >
              <p className="whitespace-pre-wrap">
                {message.content ||
                  (message.role === "assistant" && isStreaming
                    ? "Thinking..."
                    : "")}
              </p>
              {message.role === "assistant" && message.isSeekingCard ? (
                <div className="mt-3 inline-flex items-center gap-2 rounded-md border border-border/70 bg-background/50 px-3 py-1.5 text-xs text-muted-foreground">
                  <span>
                    {message.seekingLabel || "Searching for card details"}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="size-1.5 animate-bounce rounded-full bg-primary [animation-delay:0ms]" />
                    <span className="size-1.5 animate-bounce rounded-full bg-primary [animation-delay:120ms]" />
                    <span className="size-1.5 animate-bounce rounded-full bg-primary [animation-delay:240ms]" />
                  </span>
                </div>
              ) : null}
              {message.cards && message.cards.length > 0 ? (
                <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {message.cards.map((card) => (
                    <ScryfallCardOverview key={card._id} card={card} />
                  ))}
                </div>
              ) : null}
            </Card>
          ))}
          <div ref={endRef} />
        </div>
      )}
    </Card>
  );
}

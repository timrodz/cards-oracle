"use client";

import { FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { SendIcon, SparklesIcon } from "lucide-react";

interface ChatInputFormProps {
  input: string;
  isStreaming: boolean;
  apiBase: string;
  onInputChange: (value: string) => void;
  onSubmit: (query: string) => Promise<void>;
}

export function ChatInputForm({
  input,
  isStreaming,
  apiBase,
  onInputChange,
  onSubmit,
}: ChatInputFormProps) {
  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit(input);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Textarea
        value={input}
        onChange={(event) => onInputChange(event.target.value)}
        onKeyDown={(event) => {
          if (
            (event.metaKey || event.ctrlKey) &&
            event.key === "Enter" &&
            !event.shiftKey
          ) {
            event.preventDefault();
            const form = event.currentTarget.form;
            if (form) {
              form.requestSubmit();
            }
          }
        }}
        placeholder="Ask the oracle about cards, archetypes, or combos..."
        rows={3}
        disabled={isStreaming}
      />
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs text-muted-foreground">
          Streaming from {apiBase}
        </span>
        <Button type="submit" disabled={isStreaming || !input.trim()}>
          {isStreaming ? (
            <>
              <SparklesIcon />
              Streaming...
            </>
          ) : (
            <>
              <SendIcon />
              Send
            </>
          )}
        </Button>
      </div>
    </form>
  );
}

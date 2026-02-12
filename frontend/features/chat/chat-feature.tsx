"use client";

import { ChatError } from "@/features/chat/components/chat-error";
import { ChatHeader } from "@/features/chat/components/chat-header";
import { ChatInputForm } from "@/features/chat/components/chat-input-form";
import { ChatMessageList } from "@/features/chat/components/chat-message-list";
import { useChat } from "@/features/chat/viewModels/use-chat";

export function ChatFeature() {
  const {
    data: { apiBase, messages, input, isStreaming, error },
    operations: { setInput, sendMessage },
  } = useChat();

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
      <ChatHeader />
      <ChatMessageList messages={messages} isStreaming={isStreaming} />
      {error ? <ChatError error={error} /> : null}
      <ChatInputForm
        input={input}
        isStreaming={isStreaming}
        apiBase={apiBase}
        onInputChange={setInput}
        onSubmit={sendMessage}
      />
    </div>
  );
}

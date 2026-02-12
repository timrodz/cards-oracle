import {
  ElevenlabsToolScryfallCardFiltererParams,
  ElevenlabsToolScryfallCardSearchParams,
} from "@/lib/types/elevenlabs";
import { useConversation } from "@elevenlabs/react";
import { useState } from "react";

const ELEVENLABS_AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID;

interface ElevenlabsConversationProps {
  onScryfallCardSearch: (
    params: ElevenlabsToolScryfallCardSearchParams,
  ) => void;
  onScryfallCardFilterer: (
    params: ElevenlabsToolScryfallCardFiltererParams,
  ) => void;
}

export function useElevenlabsConversation({
  onScryfallCardSearch,
  onScryfallCardFilterer,
}: ElevenlabsConversationProps) {
  const [connectionStatus, setConnectionStatus] = useState<
    "connected" | "disconnected" | "connecting"
  >("disconnected");
  const [agentStatus, setAgentStatus] = useState<
    "listening" | "speaking" | "idle"
  >("idle");
  const [error, setError] = useState<string | null>(null);

  const conversation = useConversation({
    agentId: ELEVENLABS_AGENT_ID,
    onConnect: () => {
      setConnectionStatus("connected");
      setAgentStatus("listening");
      setError(null);
    },
    onDisconnect: () => {
      setConnectionStatus("disconnected");
      setAgentStatus("idle");
    },
    onError: (err) => {
      console.error(err);
      setError(typeof err === "string" ? err : "An error occurred");
      setConnectionStatus("disconnected");
      setAgentStatus("idle");
    },
    onMessage: (message) => {
      console.log("Agent Message:", message);
    },
    onDebug: (data) => {
      console.log("Agent Debug:", data);
    },
    onStatusChange: (status) => {
      console.log("Connection Status Change:", status);
      if (status.status === "connecting") {
        setConnectionStatus("connecting");
      }
    },
    onModeChange: (mode) => {
      console.log("Mode Change:", mode);
      setAgentStatus(mode.mode === "speaking" ? "speaking" : "listening");
    },
    clientTools: {
      scryfallCardSearch: onScryfallCardSearch,
      scryfallCardFilterer: onScryfallCardFilterer,
    },
  });

  const startConversation = async () => {
    if (!ELEVENLABS_AGENT_ID) {
      setError(
        "Failed to start conversation - Missing Elevenlabs configuration",
      );
      setConnectionStatus("disconnected");
      throw new Error(
        "No ElevenLabs agent configured - Please configure this in ElevenLabs.",
      );
    }
    try {
      await conversation.startSession({
        agentId: ELEVENLABS_AGENT_ID,
        connectionType: "websocket",
      });
    } catch (error) {
      console.error("Failed to start conversation:", error);
      setError(
        error instanceof Error ? error.message : "Failed to start conversation",
      );
      setConnectionStatus("disconnected");
    }
  };

  const endConversation = async () => {
    try {
      await conversation.endSession();
    } catch (error) {
      console.error("Failed to end conversation:", error);
      setError(
        error instanceof Error ? error.message : "Failed to end conversation",
      );
      setConnectionStatus("disconnected");
    }
  };

  return {
    data: {
      connectionStatus,
      agentStatus,
      error,
    },
    operations: {
      startConversation,
      endConversation,
    },
  };
}

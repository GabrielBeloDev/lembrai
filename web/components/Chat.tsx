"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage, SseEvent, ToolActivityItem, Usage } from "@/lib/types";
import { readChatStream } from "@/lib/sse";
import { MessageBubble } from "./MessageBubble";
import { ToolActivity } from "./ToolActivity";
import { Composer } from "./Composer";
import styles from "./chat.module.css";

const CHAT_ENDPOINT = "/api/ai/chat";
const NETWORK_ERROR_MESSAGE =
  "Não foi possível falar com o Assistente. Verifique se o serviço está no ar e tente novamente.";

function describeToolDetail(value: unknown): string | null {
  if (value === undefined || value === null) return null;
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function formatUsage(usage: Usage): string {
  const cost = usage.costUsd.toFixed(4);
  const seconds = usage.totalTime.toFixed(2);
  return `${usage.totalTokens} tokens · US$ ${cost} · ${seconds}s`;
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streamingText, setStreamingText] = useState("");
  const [toolActivity, setToolActivity] = useState<ToolActivityItem[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [running, setRunning] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [input, setInput] = useState("");

  const scrollAnchorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, streamingText, toolActivity, running]);

  const applyEvent = useCallback((event: SseEvent) => {
    switch (event.type) {
      case "token":
        setStreamingText((previous) => previous + event.text);
        break;
      case "tool":
        setToolActivity((previous) => [
          ...previous,
          { kind: "tool", name: event.name, detail: describeToolDetail(event.arguments) },
        ]);
        break;
      case "tool_result":
        setToolActivity((previous) => [
          ...previous,
          {
            kind: "tool_result",
            name: event.name,
            detail: describeToolDetail(event.result),
          },
        ]);
        break;
      case "tool_error":
        setToolActivity((previous) => [
          ...previous,
          { kind: "tool_error", name: event.name, detail: null },
        ]);
        break;
      case "done":
        setMessages((previous) => [
          ...previous,
          { role: "assistant", content: event.text },
        ]);
        setStreamingText("");
        setUsage(event.usage);
        break;
      case "error":
        // Keep the partial assistant text on screen but never push a broken
        // turn into history; the next request must not carry it.
        setErrorMessage(event.message);
        break;
    }
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const nextHistory: ChatMessage[] = [...messages, { role: "user", content: text }];
      setMessages(nextHistory);
      setInput("");
      setErrorMessage(null);
      setToolActivity([]);
      setStreamingText("");
      setUsage(null);
      setRunning(true);
      try {
        const response = await fetch(CHAT_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: nextHistory }),
        });
        if (!response.ok || response.body === null) {
          throw new Error(`unexpected response: ${response.status}`);
        }
        await readChatStream(response.body, applyEvent);
      } catch {
        setErrorMessage(NETWORK_ERROR_MESSAGE);
      } finally {
        setRunning(false);
      }
    },
    [messages, applyEvent],
  );

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    const canSend = trimmed.length > 0 && !running;
    if (!canSend) return;
    void sendMessage(trimmed);
  }, [input, running, sendMessage]);

  const showEmptyState = messages.length === 0 && !running;
  const showTyping =
    running && streamingText.length === 0 && toolActivity.length === 0;
  const showUsage = usage !== null && !running;

  return (
    <div className={styles.chat}>
      <header className={styles.header}>
        <h1 className={styles.title}>lembrai</h1>
        <p className={styles.subtitle}>Converse com o seu Assistente pessoal</p>
      </header>

      <div className={styles.messages} role="log" aria-live="polite">
        {showEmptyState && (
          <p className={styles.empty}>Comece a conversa com o seu Assistente.</p>
        )}

        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            role={message.role}
            content={message.content}
          />
        ))}

        {toolActivity.length > 0 && <ToolActivity items={toolActivity} />}

        {streamingText.length > 0 && (
          <MessageBubble role="assistant" content={streamingText} pending={running} />
        )}

        {showTyping && (
          <div className={styles.typing} aria-label="Assistente está digitando">
            <span />
            <span />
            <span />
          </div>
        )}

        {showUsage && <p className={styles.usage}>{formatUsage(usage)}</p>}

        {errorMessage !== null && (
          <p className={styles.error} role="alert">
            {errorMessage}
          </p>
        )}

        <div ref={scrollAnchorRef} />
      </div>

      <Composer
        value={input}
        disabled={running}
        onChange={setInput}
        onSend={handleSend}
      />
    </div>
  );
}

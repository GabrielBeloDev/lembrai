import { isFiniteNumber, isRecord, isString } from "./guards";
import type { SseEvent, Usage } from "./types";

function isNumberOrNull(value: unknown): value is number | null {
  return value === null || isFiniteNumber(value);
}

function parseUsage(value: unknown): Usage | null {
  if (!isRecord(value)) return null;
  const { prompt_tokens, completion_tokens, total_tokens, cost_usd, total_time } =
    value;
  const tokenCountsAreValid =
    isFiniteNumber(prompt_tokens) &&
    isFiniteNumber(completion_tokens) &&
    isFiniteNumber(total_tokens);
  if (!tokenCountsAreValid) return null;
  if (!isNumberOrNull(cost_usd) || !isNumberOrNull(total_time)) return null;
  return {
    promptTokens: prompt_tokens,
    completionTokens: completion_tokens,
    totalTokens: total_tokens,
    costUsd: cost_usd,
    totalTime: total_time,
  };
}

function toDoneEvent(payload: Record<string, unknown>): SseEvent | null {
  if (!isString(payload.text)) return null;
  const usage = payload.usage === null ? null : parseUsage(payload.usage);
  return { type: "done", text: payload.text, usage };
}

function toSseEvent(name: string, data: string): SseEvent | null {
  let payload: unknown;
  try {
    payload = JSON.parse(data);
  } catch {
    return null;
  }
  if (!isRecord(payload)) return null;
  switch (name) {
    case "token":
      return isString(payload.text) ? { type: "token", text: payload.text } : null;
    case "tool":
      return isString(payload.name)
        ? { type: "tool", name: payload.name, arguments: payload.arguments }
        : null;
    case "tool_result":
      return isString(payload.name)
        ? { type: "tool_result", name: payload.name, result: payload.result }
        : null;
    case "tool_error":
      return isString(payload.name)
        ? { type: "tool_error", name: payload.name }
        : null;
    case "done":
      return toDoneEvent(payload);
    case "error":
      return isString(payload.message)
        ? { type: "error", message: payload.message }
        : null;
    default:
      return null;
  }
}

function parseFrame(frame: string): SseEvent | null {
  let eventName = "";
  const dataLines: string[] = [];
  for (const rawLine of frame.split("\n")) {
    const line = rawLine.endsWith("\r") ? rawLine.slice(0, -1) : rawLine;
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).replace(/^ /, ""));
    }
  }
  if (eventName === "" || dataLines.length === 0) return null;
  return toSseEvent(eventName, dataLines.join("\n"));
}

export async function readChatStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: SseEvent) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let separatorIndex = buffer.indexOf("\n\n");
      while (separatorIndex !== -1) {
        const frame = buffer.slice(0, separatorIndex);
        buffer = buffer.slice(separatorIndex + 2);
        const event = parseFrame(frame);
        if (event) onEvent(event);
        separatorIndex = buffer.indexOf("\n\n");
      }
    }
    const trailingFrame = buffer.trim();
    if (trailingFrame !== "") {
      const event = parseFrame(trailingFrame);
      if (event) onEvent(event);
    }
  } finally {
    reader.releaseLock();
  }
}

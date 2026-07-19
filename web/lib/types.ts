export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface Usage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  costUsd: number;
  totalTime: number;
}

export type ToolActivityKind = "tool" | "tool_result" | "tool_error";

export interface ToolActivityItem {
  kind: ToolActivityKind;
  name: string;
  detail: string | null;
}

export type SseEvent =
  | { type: "token"; text: string }
  | { type: "tool"; name: string; arguments: unknown }
  | { type: "tool_result"; name: string; result: unknown }
  | { type: "tool_error"; name: string }
  | { type: "done"; text: string; usage: Usage | null }
  | { type: "error"; message: string };

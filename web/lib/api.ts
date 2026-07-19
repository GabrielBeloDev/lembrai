import { isBoolean, isRecord, isString } from "./guards";
import type {
  OnboardingQuestion,
  Profile,
  Reminder,
  StoredNote,
} from "./types";

const API_BASE = "/api/ai";
const INVALID_RESPONSE = "resposta inesperada do servidor";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number) {
    super(`request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
  }
}

function jsonRequest(body: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

async function requestJson(path: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) throw new ApiError(response.status);
  const data: unknown = await response.json();
  return data;
}

function parseProfile(value: unknown): Profile {
  if (!isRecord(value)) throw new Error(INVALID_RESPONSE);
  const content = value.content;
  if (content === null) return { content: null };
  if (isString(content)) return { content };
  throw new Error(INVALID_RESPONSE);
}

function parseQuestion(value: unknown): OnboardingQuestion {
  if (isRecord(value) && isString(value.title) && isString(value.question)) {
    return { title: value.title, question: value.question };
  }
  throw new Error(INVALID_RESPONSE);
}

function parseNote(value: unknown): StoredNote {
  if (isRecord(value) && isString(value.id) && isString(value.text)) {
    return { id: value.id, text: value.text };
  }
  throw new Error(INVALID_RESPONSE);
}

function parseReminder(value: unknown): Reminder {
  if (
    isRecord(value) &&
    isString(value.id) &&
    isString(value.message) &&
    isString(value.due) &&
    isString(value.created_at) &&
    isBoolean(value.delivered)
  ) {
    return {
      id: value.id,
      message: value.message,
      due: value.due,
      createdAt: value.created_at,
      delivered: value.delivered,
    };
  }
  throw new Error(INVALID_RESPONSE);
}

function parseNoteId(value: unknown): { id: string } {
  if (isRecord(value) && isString(value.id)) return { id: value.id };
  throw new Error(INVALID_RESPONSE);
}

function parseStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) throw new Error(INVALID_RESPONSE);
  const result: string[] = [];
  for (const item of value) {
    if (!isString(item)) throw new Error(INVALID_RESPONSE);
    result.push(item);
  }
  return result;
}

function parseArray<T>(value: unknown, parseItem: (item: unknown) => T): T[] {
  if (!Array.isArray(value)) throw new Error(INVALID_RESPONSE);
  return value.map(parseItem);
}

export async function getProfile(): Promise<Profile> {
  return parseProfile(await requestJson("/profile"));
}

export async function getQuestions(): Promise<OnboardingQuestion[]> {
  return parseArray(await requestJson("/onboarding/questions"), parseQuestion);
}

export async function postProfile(answers: string[]): Promise<Profile> {
  return parseProfile(await requestJson("/profile", jsonRequest({ answers })));
}

export async function getNotes(): Promise<StoredNote[]> {
  return parseArray(await requestJson("/notes"), parseNote);
}

export async function postNote(text: string): Promise<{ id: string }> {
  return parseNoteId(await requestJson("/notes", jsonRequest({ text })));
}

export async function getReminders(): Promise<Reminder[]> {
  return parseArray(await requestJson("/reminders"), parseReminder);
}

export async function deliverReminders(): Promise<string[]> {
  const data = await requestJson("/reminders/deliver", { method: "POST" });
  if (!isRecord(data)) throw new Error(INVALID_RESPONSE);
  return parseStringArray(data.delivered);
}

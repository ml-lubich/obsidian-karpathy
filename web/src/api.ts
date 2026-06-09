import type { ChatMessage, GraphData, LLMStatus } from "./types";

const BASE = "";

async function _json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchGraph(): Promise<GraphData> {
  return _json<GraphData>(await fetch(`${BASE}/api/graph`));
}

export async function fetchLLMStatus(): Promise<LLMStatus> {
  return _json<LLMStatus>(await fetch(`${BASE}/api/llm-status`));
}

export async function sendChat(messages: ChatMessage[]): Promise<string> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  const data = await _json<{ reply: string }>(res);
  return data.reply;
}

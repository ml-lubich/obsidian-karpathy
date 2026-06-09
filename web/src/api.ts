import type {
  ChatMessage,
  ChatMode,
  GraphData,
  JobRecord,
  LLMSettingsInput,
  LLMStatus,
} from "./types";

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

export async function sendChat(messages: ChatMessage[], mode: ChatMode, focusNodeId: string): Promise<string> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, mode, focus_node_id: focusNodeId }),
  });
  const data = await _json<{ reply: string }>(res);
  return data.reply;
}

export async function saveLLMSettings(input: LLMSettingsInput): Promise<LLMStatus> {
  const res = await fetch(`${BASE}/api/settings/llm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return _json<LLMStatus>(res);
}

export async function fetchJobs(): Promise<JobRecord[]> {
  return _json<JobRecord[]>(await fetch(`${BASE}/api/jobs`));
}

export async function launchSummarizeJob(nodeId: string): Promise<JobRecord> {
  const res = await fetch(`${BASE}/api/jobs/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ node_id: nodeId }),
  });
  return _json<JobRecord>(res);
}

export async function launchPruneJob(): Promise<JobRecord> {
  const res = await fetch(`${BASE}/api/jobs/prune`, { method: "POST" });
  return _json<JobRecord>(res);
}

export async function launchPipelineJob(nodeId: string): Promise<JobRecord> {
  const res = await fetch(`${BASE}/api/jobs/pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ node_id: nodeId }),
  });
  return _json<JobRecord>(res);
}

export async function runNextJob(): Promise<JobRecord | { status: "idle"; detail: string }> {
  const res = await fetch(`${BASE}/api/jobs/run-next`, { method: "POST" });
  return _json<JobRecord | { status: "idle"; detail: string }>(res);
}

export async function cancelJob(jobId: string): Promise<JobRecord> {
  const res = await fetch(`${BASE}/api/jobs/${jobId}/cancel`, { method: "POST" });
  return _json<JobRecord>(res);
}

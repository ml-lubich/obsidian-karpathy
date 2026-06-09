export interface GraphNode {
  id: string;
  title: string;
  label: string;
  kind: "note" | "tag" | "missing";
  path?: string;
  summary?: string;
  markdown?: string;
  markdown_length?: number;
  tags?: string[];
  word_count?: number;
  backlinks?: number;
  outlinks?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  kind: "wiki" | "markdown" | "tag";
  label?: string;
}

export interface GraphStats {
  vault: string;
  notes: number;
  edges: number;
  tags: number;
  missing: number;
  words: number;
  average_words: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: GraphStats;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface LLMStatus {
  enabled: boolean;
  model: string;
  base_url: string;
  mode: ChatMode;
  api_key_source?: string;
}

export type ChatMode = "basic" | "rag" | "tools";

export interface LLMSettingsInput {
  api_key: string;
  base_url: string;
  model: string;
  mode: ChatMode;
}

export interface JobRecord {
  id: string;
  type: "summarize" | "prune" | "pipeline";
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;
  started_at?: string;
  finished_at?: string;
  node_id?: string;
  error?: string;
  result: Record<string, unknown>;
}

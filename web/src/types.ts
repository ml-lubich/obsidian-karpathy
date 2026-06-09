export interface GraphNode {
  id: string;
  title: string;
  kind: "note" | "tag" | "missing";
  path?: string;
  summary?: string;
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
}

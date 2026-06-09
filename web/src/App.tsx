import { useEffect, useState } from "react";
import { fetchGraph, fetchLLMStatus } from "./api";
import type { GraphData, GraphNode, LLMStatus } from "./types";
import { Graph } from "./components/Graph";
import { Sidebar } from "./components/Sidebar";
import { RightPanel } from "./components/RightPanel";
import "./styles.css";

export function App() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [llmStatus, setLLMStatus] = useState<LLMStatus | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    fetchGraph().then(setGraph).catch((e: Error) => setError(e.message));
    fetchLLMStatus().then(setLLMStatus).catch((e: Error) => {
      console.error("Failed to fetch LLM status", e);
      setLLMStatus({ enabled: false, model: "", base_url: "" });
    });
  }, []);

  if (error) return <div className="error-screen">{error}</div>;
  if (!graph) return <div className="loading-screen">Loading vault…</div>;

  return (
    <main className="shell">
      <Sidebar
        stats={graph.stats}
        filter={filter}
        search={search}
        llmStatus={llmStatus}
        onFilter={setFilter}
        onSearch={setSearch}
      />
      <section className="canvas-wrap" aria-label="Knowledge graph">
        <Graph
          graph={graph}
          filter={filter}
          search={search}
          selected={selected}
          onSelect={setSelected}
        />
      </section>
      <RightPanel selected={selected} llmEnabled={llmStatus?.enabled ?? false} />
    </main>
  );
}

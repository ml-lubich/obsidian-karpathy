import { useEffect, useState } from "react";
import { fetchGraph, fetchLLMStatus } from "./api";
import type { ChatMode, GraphData, GraphNode, LLMProvider, LLMStatus } from "./types";
import { Graph } from "./components/Graph";
import { Sidebar } from "./components/Sidebar";
import { RightPanel } from "./components/RightPanel";
import "./styles.css";

const THEME_KEY = "okg-theme";

function _storedTheme(): "dark" | "light" {
  const stored = window.localStorage.getItem(THEME_KEY);
  return stored === "light" ? "light" : "dark";
}

export function App() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [llmStatus, setLLMStatus] = useState<LLMStatus | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [theme, setTheme] = useState<"dark" | "light">(() => _storedTheme());
  const [chatMode, setChatMode] = useState<ChatMode>("rag");
  const [chatModel, setChatModel] = useState<string>("gpt-4o-mini");
  const [chatBaseUrl, setChatBaseUrl] = useState<string>("https://api.openai.com/v1");
  const [chatProvider, setChatProvider] = useState<LLMProvider>("openai");
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    fetchGraph().then(setGraph).catch((e: Error) => setError(e.message));
    fetchLLMStatus()
      .then((status) => {
        setLLMStatus(status);
        setChatMode(status.mode);
        setChatModel(status.model);
        setChatBaseUrl(status.base_url);
        setChatProvider(status.provider ?? "openai");
      })
      .catch((e: Error) => {
        console.error("Failed to fetch LLM status", e);
        setLLMStatus({ enabled: false, model: "", base_url: "", mode: "rag", provider: "openai" });
      });
  }, []);

  useEffect(() => {
    document.body.dataset.theme = theme;
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

  const handleSettingsSaved = (status: LLMStatus) => {
    setChatMode(status.mode);
    setChatModel(status.model);
    setChatBaseUrl(status.base_url);
    setChatProvider(status.provider ?? "openai");
    setLLMStatus(status);
  };

  if (error) return <div className="error-screen">{error}</div>;
  if (!graph) return <div className="loading-screen">Loading vault…</div>;

  return (
    <main className="shell">
      <Sidebar
        stats={graph.stats}
        filter={filter}
        search={search}
        theme={theme}
        llmStatus={llmStatus}
        onFilter={setFilter}
        onSearch={setSearch}
        onToggleTheme={toggleTheme}
      />
      <section className="canvas-wrap" aria-label="Knowledge graph">
        <Graph graph={graph} filter={filter} search={search} selected={selected} onSelect={setSelected} />
      </section>
      <RightPanel
        graph={graph}
        selected={selected}
        llmEnabled={llmStatus?.enabled ?? false}
        mode={chatMode}
        model={chatModel}
        baseUrl={chatBaseUrl}
        provider={chatProvider}
        onSelect={setSelected}
        onSettingsSaved={handleSettingsSaved}
      />
    </main>
  );
}

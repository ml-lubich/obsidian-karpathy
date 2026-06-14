import { useState } from "react";
import type { ChatMode, GraphData, GraphNode, LLMProvider, LLMStatus } from "../types";
import { Inspector } from "./Inspector";
import { Chat } from "./Chat";
import { Settings } from "./Settings";

interface Props {
  graph: GraphData;
  selected: GraphNode | null;
  llmEnabled: boolean;
  mode: ChatMode;
  model: string;
  baseUrl: string;
  provider: LLMProvider;
  onSelect: (node: GraphNode | null) => void;
  onSettingsSaved: (status: LLMStatus) => void;
}

type Tab = "inspector" | "chat" | "settings";

export function RightPanel({ graph, selected, llmEnabled, mode, model, baseUrl, provider, onSelect, onSettingsSaved }: Props) {
  const [tab, setTab] = useState<Tab>("inspector");

  return (
    <aside className="panel inspector">
      <div className="tab-bar">
        <button className={`tab${tab === "inspector" ? " active" : ""}`} onClick={() => setTab("inspector")}>
          Inspector
        </button>
        <button className={`tab${tab === "chat" ? " active" : ""}`} onClick={() => setTab("chat")}>
          AI Chat {llmEnabled ? "✓" : ""}
        </button>
        <button className={`tab${tab === "settings" ? " active" : ""}`} onClick={() => setTab("settings")}>
          Settings
        </button>
      </div>
      <div className="tab-content">
        {tab === "inspector" && <Inspector node={selected} graph={graph} onSelect={onSelect} />}
        {tab === "chat" && <Chat enabled={llmEnabled} mode={mode} focusNodeId={selected?.id ?? ""} />}
        {tab === "settings" && (
          <Settings
            selectedNodeId={selected?.id ?? ""}
            mode={mode}
            model={model}
            baseUrl={baseUrl}
            provider={provider}
            onSettingsSaved={onSettingsSaved}
          />
        )}
      </div>
    </aside>
  );
}

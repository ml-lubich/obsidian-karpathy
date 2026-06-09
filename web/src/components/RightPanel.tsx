import { useState } from "react";
import type { GraphNode } from "../types";
import { Inspector } from "./Inspector";
import { Chat } from "./Chat";

interface Props {
  selected: GraphNode | null;
  llmEnabled: boolean;
}

type Tab = "inspector" | "chat";

export function RightPanel({ selected, llmEnabled }: Props) {
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
      </div>
      <div className="tab-content">
        {tab === "inspector" ? (
          <Inspector node={selected} />
        ) : (
          <Chat enabled={llmEnabled} />
        )}
      </div>
    </aside>
  );
}

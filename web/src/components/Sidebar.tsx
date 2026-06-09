import type { GraphStats, LLMStatus } from "../types";

interface Props {
  stats: GraphStats;
  filter: string;
  search: string;
  theme: "dark" | "light";
  llmStatus: LLMStatus | null;
  onFilter: (f: string) => void;
  onSearch: (s: string) => void;
  onToggleTheme: () => void;
}

const FILTERS = ["all", "note", "tag", "missing"] as const;

function StatItem({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="stat">
      <b>{value ?? 0}</b>
      <span>{label}</span>
    </div>
  );
}

function LLMBadge({ status }: { status: LLMStatus | null }) {
  if (!status) return null;
  const cls = status.enabled ? "llm-badge llm-on" : "llm-badge llm-off";
  const label = status.enabled ? `LLM: ${status.model}` : "LLM: not configured";
  return <div className={cls}>{label}</div>;
}

export function Sidebar({ stats, filter, search, theme, llmStatus, onFilter, onSearch, onToggleTheme }: Props) {
  return (
    <aside className="panel sidebar">
      <div className="brand">
        <div className="mark">OK</div>
        <div>
          <p className="eyebrow">Obsidian Graph</p>
          <h1>Knowledge Map</h1>
        </div>
      </div>

      <button className="theme-toggle" onClick={onToggleTheme}>
        {theme === "dark" ? "☀ Light mode" : "🌙 Dark mode"}
      </button>

      <label className="search">
        <span>Search</span>
        <input
          type="search"
          placeholder="Notes, tags, links…"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
        />
      </label>

      <div className="filters" aria-label="Node filters">
        {FILTERS.map((f) => (
          <button
            key={f}
            className={`filter${filter === f ? " active" : ""}`}
            onClick={() => onFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="stats">
        <StatItem label="Notes" value={stats.notes} />
        <StatItem label="Edges" value={stats.edges} />
        <StatItem label="Tags" value={stats.tags} />
        <StatItem label="Missing" value={stats.missing} />
        <StatItem label="Words" value={stats.words} />
        <StatItem label="Avg Words" value={stats.average_words} />
      </div>

      <LLMBadge status={llmStatus} />
    </aside>
  );
}

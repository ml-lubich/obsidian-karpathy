import { useEffect, useState } from "react";
import {
  cancelJob,
  fetchJobs,
  launchPipelineJob,
  launchPruneJob,
  launchSummarizeJob,
  runNextJob,
  saveLLMSettings,
} from "../api";
import type { ChatMode, JobRecord, LLMProvider, LLMSettingsInput, LLMStatus } from "../types";

interface Props {
  selectedNodeId: string;
  mode: ChatMode;
  model: string;
  baseUrl: string;
  provider: LLMProvider;
  onSettingsSaved: (status: LLMStatus) => void;
}

const MODES: ChatMode[] = ["basic", "rag", "tools"];

const PRESET_MODELS: Record<string, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini"],
  anthropic: [
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
  ],
  custom: [],
};

const PROVIDER_DEFAULTS: Record<string, { base_url: string; model: string }> = {
  openai: { base_url: "https://api.openai.com/v1", model: "gpt-4o-mini" },
  anthropic: { base_url: "", model: "claude-sonnet-4-6" },
  custom: { base_url: "", model: "" },
};

type ProviderTab = LLMProvider | "custom";

function _detectTab(provider: LLMProvider, baseUrl: string): ProviderTab {
  if (provider === "anthropic") return "anthropic";
  const isDefault = !baseUrl || baseUrl === "https://api.openai.com/v1";
  return isDefault ? "openai" : "custom";
}

function _fmtResult(job: JobRecord): string {
  if (job.error) return `Error: ${job.error}`;
  if (job.type === "summarize") return String(job.result.summary ?? "Summary ready.");
  if (job.type === "prune") return `Prune candidates: ${Number(job.result.candidate_count ?? 0)}`;
  if (job.type === "pipeline") return "Pipeline completed.";
  return "Job finished.";
}

function _isCancelable(job: JobRecord): boolean {
  return job.status === "queued" || job.status === "running";
}

function _initial(mode: ChatMode, model: string, baseUrl: string, provider: LLMProvider): LLMSettingsInput {
  return { api_key: "", base_url: baseUrl, model, mode, provider };
}

export function Settings({ selectedNodeId, mode, model, baseUrl, provider, onSettingsSaved }: Props) {
  const [form, setForm] = useState<LLMSettingsInput>(() => _initial(mode, model, baseUrl, provider));
  const [tab, setTab] = useState<ProviderTab>(() => _detectTab(provider, baseUrl));
  const [customModelId, setCustomModelId] = useState("");
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [statusMsg, setStatusMsg] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(_initial(mode, model, baseUrl, provider));
    setTab(_detectTab(provider, baseUrl));
  }, [mode, model, baseUrl, provider]);

  useEffect(() => {
    fetchJobs().then(setJobs).catch(() => setJobs([]));
  }, []);

  const refreshJobs = async () => {
    const next = await fetchJobs().catch(() => []);
    setJobs(next);
  };

  const switchTab = (next: ProviderTab) => {
    setTab(next);
    const defaults = PROVIDER_DEFAULTS[next];
    const resolvedProvider: LLMProvider = next === "custom" ? "openai" : next;
    setForm({ ...form, provider: resolvedProvider, base_url: defaults.base_url, model: defaults.model });
    setCustomModelId("");
  };

  const presets = PRESET_MODELS[tab] ?? [];
  const useCustomModel = customModelId !== "" || (presets.length > 0 && form.model !== "" && !presets.includes(form.model));

  const pickModel = (val: string) => {
    if (val === "__custom__") {
      setCustomModelId(form.model);
      setForm({ ...form, model: "" });
    } else {
      setCustomModelId("");
      setForm({ ...form, model: val });
    }
  };

  const save = async () => {
    if (saving) return;
    setSaving(true);
    setStatusMsg("");
    const payload = { ...form, model: useCustomModel && customModelId ? customModelId : form.model };
    const next = await saveLLMSettings(payload).catch((e: Error) => { setStatusMsg(e.message); return null; });
    if (next) {
      onSettingsSaved(next);
      setStatusMsg("Connected.");
      setForm({ ...payload, api_key: "" });
    }
    setSaving(false);
  };

  const runSummarize = async () => {
    if (!selectedNodeId) { setStatusMsg("Select a note node first."); return; }
    const job = await launchSummarizeJob(selectedNodeId).catch((e: Error) => { setStatusMsg(e.message); return null; });
    if (job) { setStatusMsg("Queued summarize job."); await refreshJobs(); }
  };

  const runPrune = async () => {
    const job = await launchPruneJob().catch((e: Error) => { setStatusMsg(e.message); return null; });
    if (job) { setStatusMsg("Queued prune job."); await refreshJobs(); }
  };

  const runPipeline = async () => {
    if (!selectedNodeId) { setStatusMsg("Select a note node first."); return; }
    const job = await launchPipelineJob(selectedNodeId).catch((e: Error) => { setStatusMsg(e.message); return null; });
    if (job) { setStatusMsg("Queued pipeline job."); await refreshJobs(); }
  };

  const runNext = async () => {
    const result = await runNextJob().catch((e: Error) => { setStatusMsg(e.message); return null; });
    if (result) {
      const idle = "status" in result && result.status === "idle";
      setStatusMsg(idle ? String((result as { detail: string }).detail) : `Ran job: ${"type" in result ? result.type : ""}`);
      await refreshJobs();
    }
  };

  const cancelOne = async (jobId: string) => {
    const cancelled = await cancelJob(jobId).catch((e: Error) => { setStatusMsg(e.message); return null; });
    if (cancelled) { setStatusMsg(`Cancelled job: ${cancelled.type}`); await refreshJobs(); }
  };

  return (
    <div className="settings-wrap">
      <h2>AI Settings</h2>

      <div className="provider-tabs">
        {(["openai", "anthropic", "custom"] as ProviderTab[]).map((t) => (
          <button type="button" key={t} className={`provider-tab${tab === t ? " active" : ""}`} onClick={() => switchTab(t)}>
            {t === "openai" ? "OpenAI" : t === "anthropic" ? "Anthropic" : "Custom / Local"}
          </button>
        ))}
      </div>

      <p className="provider-hint">
        {tab === "openai" && "OpenAI API — paste your sk-… key below."}
        {tab === "anthropic" && "Anthropic Claude API — paste your sk-ant-… key below."}
        {tab === "custom" && "Any OpenAI-compatible endpoint: Ollama, LM Studio, Groq, OpenRouter… API key is optional for local servers."}
      </p>

      <label className="settings-field">
        <span>
          {tab === "anthropic" ? "Anthropic API Key" : tab === "openai" ? "OpenAI API Key" : "API Key (optional)"}
        </span>
        <input
          type="password"
          placeholder={tab === "anthropic" ? "sk-ant-…" : tab === "openai" ? "sk-…" : "leave blank for Ollama / LM Studio"}
          value={form.api_key}
          onChange={(e) => setForm({ ...form, api_key: e.target.value })}
        />
      </label>

      {tab === "custom" && (
        <label className="settings-field">
          <span>Base URL</span>
          <input
            placeholder="http://localhost:11434/v1"
            value={form.base_url}
            onChange={(e) => setForm({ ...form, base_url: e.target.value })}
          />
        </label>
      )}

      <label className="settings-field">
        <span>Model</span>
        {presets.length > 0 ? (
          <select value={useCustomModel ? "__custom__" : form.model} onChange={(e) => pickModel(e.target.value)}>
            {presets.map((m) => <option key={m} value={m}>{m}</option>)}
            <option value="__custom__">Custom model ID…</option>
          </select>
        ) : (
          <input
            placeholder="llama3.2, mistral, custom-model…"
            value={form.model}
            onChange={(e) => setForm({ ...form, model: e.target.value })}
          />
        )}
      </label>

      {useCustomModel && presets.length > 0 && (
        <label className="settings-field">
          <span>Custom model ID</span>
          <input
            placeholder="exact model string"
            value={customModelId}
            onChange={(e) => setCustomModelId(e.target.value)}
          />
        </label>
      )}

      <label className="settings-field">
        <span>Chat mode</span>
        <select value={form.mode} onChange={(e) => setForm({ ...form, mode: e.target.value as ChatMode })}>
          {MODES.map((m) => (
            <option key={m} value={m}>
              {m === "rag" ? "RAG (retrieval-augmented)" : m === "basic" ? "Basic (full vault context)" : "Tools (action-oriented)"}
            </option>
          ))}
        </select>
      </label>

      <button type="button" className="settings-btn primary settings-save" onClick={save} disabled={saving}>
        {saving ? "Saving…" : "Save & Connect"}
      </button>

      {statusMsg && <p className="settings-status">{statusMsg}</p>}

      <hr className="settings-divider" />
      <h3>Vault Jobs</h3>
      <p className="provider-hint">Select a note in the graph first, then run jobs against it.</p>
      <div className="settings-actions">
        <button type="button" className="settings-btn" onClick={runSummarize}>Summarize note</button>
        <button type="button" className="settings-btn" onClick={runPrune}>Find prune candidates</button>
        <button type="button" className="settings-btn" onClick={runPipeline}>Run pipeline</button>
        <button type="button" className="settings-btn" onClick={runNext}>Run next queued job</button>
      </div>

      <h3>Recent jobs</h3>
      <div className="job-list">
        {jobs.length === 0 && <p className="provider-hint">No jobs yet.</p>}
        {jobs.slice(0, 10).map((job) => (
          <div className="job-item" key={job.id}>
            <b>{job.type} · {job.status}</b>
            <small>{new Date(job.created_at).toLocaleString()}</small>
            <p>{_fmtResult(job)}</p>
            {_isCancelable(job) && (
              <button type="button" className="settings-btn" onClick={() => cancelOne(job.id)}>Cancel</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

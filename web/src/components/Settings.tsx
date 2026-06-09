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
import type { ChatMode, JobRecord, LLMSettingsInput, LLMStatus } from "../types";

interface Props {
  selectedNodeId: string;
  mode: ChatMode;
  model: string;
  baseUrl: string;
  onSettingsSaved: (status: LLMStatus) => void;
}

const MODES: ChatMode[] = ["basic", "rag", "tools"];

function _fmtResult(job: JobRecord): string {
  if (job.error) return `Error: ${job.error}`;
  if (job.type === "summarize") return String(job.result.summary ?? "Summary ready.");
  if (job.type === "prune") {
    const count = Number(job.result.candidate_count ?? 0);
    return `Prune candidates: ${count}`;
  }
  if (job.type === "pipeline") return "Pipeline completed.";
  return "Job finished.";
}


function _isCancelable(job: JobRecord): boolean {
  return job.status === "queued" || job.status === "running";
}

function _initial(mode: ChatMode, model: string, baseUrl: string): LLMSettingsInput {
  return { api_key: "", base_url: baseUrl, model, mode };
}

export function Settings({ selectedNodeId, mode, model, baseUrl, onSettingsSaved }: Props) {
  const [form, setForm] = useState<LLMSettingsInput>(() => _initial(mode, model, baseUrl));
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [status, setStatus] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(_initial(mode, model, baseUrl));
  }, [mode, model, baseUrl]);

  useEffect(() => {
    fetchJobs().then(setJobs).catch(() => setJobs([]));
  }, []);

  const refreshJobs = async () => {
    const next = await fetchJobs().catch(() => []);
    setJobs(next);
  };

  const save = async () => {
    if (saving) return;
    setSaving(true);
    setStatus("");
    const next = await saveLLMSettings(form).catch((e: Error) => {
      setStatus(e.message);
      return null;
    });
    if (next) {
      onSettingsSaved(next);
      setStatus("Saved settings.");
      setForm({ ...form, api_key: "" });
    }
    setSaving(false);
  };

  const runSummarize = async () => {
    if (!selectedNodeId) {
      setStatus("Select a note node first.");
      return;
    }
    const job = await launchSummarizeJob(selectedNodeId).catch((e: Error) => {
      setStatus(e.message);
      return null;
    });
    if (job) {
      setStatus("Queued summarize job.");
      await refreshJobs();
    }
  };

  const runPrune = async () => {
    const job = await launchPruneJob().catch((e: Error) => {
      setStatus(e.message);
      return null;
    });
    if (job) {
      setStatus("Queued prune job.");
      await refreshJobs();
    }
  };

  const runPipeline = async () => {
    if (!selectedNodeId) {
      setStatus("Select a note node first.");
      return;
    }
    const job = await launchPipelineJob(selectedNodeId).catch((e: Error) => {
      setStatus(e.message);
      return null;
    });
    if (job) {
      setStatus("Queued pipeline job.");
      await refreshJobs();
    }
  };

  const runNext = async () => {
    const result = await runNextJob().catch((e: Error) => {
      setStatus(e.message);
      return null;
    });
    if (result) {
      setStatus(result.status === "idle" ? result.detail : `Ran job: ${result.type}`);
      await refreshJobs();
    }
  };

  const cancel = async (jobId: string) => {
    const cancelled = await cancelJob(jobId).catch((e: Error) => {
      setStatus(e.message);
      return null;
    });
    if (cancelled) {
      setStatus(`Cancelled job: ${cancelled.type}`);
      await refreshJobs();
    }
  };

  return (
    <div className="settings-wrap">
      <h2>Agent & LLM Settings</h2>
      <p>Configure chat mode, endpoint, and run vault jobs.</p>

      <label className="settings-field">
        <span>Chat mode</span>
        <select value={form.mode} onChange={(e) => setForm({ ...form, mode: e.target.value as ChatMode })}>
          {MODES.map((candidateMode) => (
            <option key={candidateMode} value={candidateMode}>{candidateMode}</option>
          ))}
        </select>
      </label>

      <label className="settings-field">
        <span>Model</span>
        <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
      </label>

      <label className="settings-field">
        <span>Base URL</span>
        <input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
      </label>

      <label className="settings-field">
        <span>API key (kept in memory on backend)</span>
        <input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
      </label>

      <div className="settings-actions">
        <button className="settings-btn" onClick={save} disabled={saving}>Save LLM settings</button>
        <button className="settings-btn" onClick={runSummarize}>Queue summarization job</button>
        <button className="settings-btn" onClick={runPrune}>Queue prune job</button>
        <button className="settings-btn" onClick={runPipeline}>Queue pipeline job</button>
        <button className="settings-btn" onClick={runNext}>Run next queued job</button>
      </div>

      {status && <p className="settings-status">{status}</p>}

      <h3>Recent jobs</h3>
      <div className="job-list">
        {jobs.slice(0, 10).map((job) => (
          <div className="job-item" key={job.id}>
            <b>{job.type} · {job.status}</b>
            <small>{new Date(job.created_at).toLocaleString()}</small>
            <p>{_fmtResult(job)}</p>
            {_isCancelable(job) && (
              <button className="settings-btn" onClick={() => cancel(job.id)}>
                Cancel
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

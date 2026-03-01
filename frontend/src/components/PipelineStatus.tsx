import { useEffect, useState } from "react";
import { getPipelineStatus, triggerPipelineUpdate } from "../api/client";
import type { PipelineStatus as PipelineStatusType } from "../types";

const STAGE_LABELS: Record<string, string> = {
  idle: "Idle",
  starting: "Starting...",
  scraping: "Scraping Eventbrite...",
  classifying: "Classifying events with BART...",
  embedding: "Generating embeddings...",
  recommending: "Building recommendations...",
};

export default function PipelineStatus() {
  const [status, setStatus] = useState<PipelineStatusType | null>(null);
  const [error, setError] = useState("");

  async function fetchStatus() {
    try {
      const s = await getPipelineStatus();
      setStatus(s);
    } catch {
      // ignore fetch errors
    }
  }

  useEffect(() => {
    fetchStatus();
  }, []);

  // Poll every 60s when running
  useEffect(() => {
    if (!status?.is_running) return;
    const interval = setInterval(fetchStatus, 60_000);
    return () => clearInterval(interval);
  }, [status?.is_running]);

  async function handleUpdate() {
    setError("");
    try {
      const s = await triggerPipelineUpdate();
      setStatus(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start pipeline");
    }
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <h3 className="text-white font-semibold text-sm mb-3">Event Pipeline</h3>

      <div className="flex items-center gap-2 mb-2">
        <span
          className={`w-2.5 h-2.5 rounded-full ${
            status?.is_running ? "bg-yellow-400 animate-pulse" : "bg-green-500"
          }`}
        />
        <span className="text-gray-300 text-sm">
          {status ? STAGE_LABELS[status.stage] || status.stage : "Loading..."}
        </span>
      </div>

      {status?.last_updated && (
        <p className="text-gray-500 text-xs mb-2">
          Last updated: {new Date(status.last_updated).toLocaleString()}
        </p>
      )}

      {status?.last_error && (
        <p className="text-red-400 text-xs mb-2">Error: {status.last_error}</p>
      )}

      {error && <p className="text-red-400 text-xs mb-2">{error}</p>}

      <button
        onClick={handleUpdate}
        disabled={status?.is_running}
        className={`w-full py-2 px-4 rounded-md text-sm font-medium transition-colors ${
          status?.is_running
            ? "bg-gray-600 text-gray-400 cursor-not-allowed"
            : "bg-indigo-600 text-white hover:bg-indigo-700"
        }`}
      >
        {status?.is_running ? "Pipeline Running..." : "Update Events"}
      </button>
    </div>
  );
}

import type {
  EventRecommendation,
  LabelsResponse,
  PipelineStatus,
  UserListResponse,
  UserRecommendationsResponse,
} from "../types";

const BASE = "/api";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

// --- Labels ---
export function getLabels(): Promise<LabelsResponse> {
  return fetchJSON(`${BASE}/recommend/labels`);
}

// --- New User ---
export function getRecommendationsForLabels(
  selectedLabels: string[],
  topN: number = 10
): Promise<{ selected_labels: string[]; recommended_events: EventRecommendation[] }> {
  return fetchJSON(`${BASE}/recommend/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected_labels: selectedLabels, top_n: topN }),
  });
}

// --- Admin ---
export function getUsers(
  search: string = "",
  limit: number = 50,
  offset: number = 0
): Promise<UserListResponse> {
  const params = new URLSearchParams({
    search,
    limit: String(limit),
    offset: String(offset),
  });
  return fetchJSON(`${BASE}/admin/users?${params}`);
}

export function getUserRecommendations(
  userId: string
): Promise<UserRecommendationsResponse> {
  return fetchJSON(`${BASE}/admin/users/${encodeURIComponent(userId)}/recommendations`);
}

// --- Pipeline ---
export function triggerPipelineUpdate(): Promise<PipelineStatus> {
  return fetchJSON(`${BASE}/pipeline/update`, { method: "POST" });
}

export function getPipelineStatus(): Promise<PipelineStatus> {
  return fetchJSON(`${BASE}/pipeline/status`);
}

// --- LLM Reranker ---
export function rerankEvents(
  events: EventRecommendation[],
  prompt: string
): Promise<{ events: EventRecommendation[]; llm_applied: boolean; message: string }> {
  return fetchJSON(`${BASE}/llm/rerank`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ events, prompt }),
  });
}

import type {
  Collection,
  EventRecommendation,
  LabelsResponse,
  PipelineStatus,
  Section,
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

// --- Collections ---
export function getCollections(): Promise<{ collections: Collection[] }> {
  return fetchJSON(`${BASE}/admin/collections`);
}

export function createCollection(
  name: string,
  labels: string[]
): Promise<Collection> {
  return fetchJSON(`${BASE}/admin/collections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, labels }),
  });
}

export function generateCollection(
  description: string
): Promise<{ collection: Collection; description: string }> {
  return fetchJSON(`${BASE}/admin/collections/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });
}

// --- Pipeline ---
export function triggerPipelineUpdate(): Promise<PipelineStatus> {
  return fetchJSON(`${BASE}/pipeline/update`, { method: "POST" });
}

export function getPipelineStatus(): Promise<PipelineStatus> {
  return fetchJSON(`${BASE}/pipeline/status`);
}

// --- Save New User ---
export function saveNewUser(
  name: string,
  selectedLabels: string[],
  recommendedEvents: EventRecommendation[]
): Promise<{ saved: boolean; name: string; message: string }> {
  return fetchJSON(`${BASE}/recommend/save-user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name,
      selected_labels: selectedLabels,
      recommended_events: recommendedEvents,
    }),
  });
}

// --- Sections (ephemeral) ---
export function getSections(): Promise<{ sections: Section[] }> {
  return fetchJSON(`${BASE}/admin/sections`);
}

export function createSection(
  description: string
): Promise<{ section: Section }> {
  return fetchJSON(`${BASE}/admin/sections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });
}

export function deleteSection(sectionId: string): Promise<{ deleted: boolean }> {
  return fetchJSON(`${BASE}/admin/sections/${sectionId}`, {
    method: "DELETE",
  });
}

export function mapSectionEvents(
  sectionId: string,
  events: EventRecommendation[]
): Promise<{ section_id: string; title: string; events: EventRecommendation[] }> {
  return fetchJSON(`${BASE}/admin/sections/${sectionId}/map`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ events }),
  });
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

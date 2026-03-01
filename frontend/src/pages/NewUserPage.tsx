import { useEffect, useState } from "react";
import {
  getLabels,
  getRecommendationsForLabels,
  rerankEvents,
  saveNewUser,
} from "../api/client";
import EventList from "../components/EventList";
import LabelSelector from "../components/LabelSelector";
import type { EventRecommendation } from "../types";

export default function NewUserPage() {
  const [groups, setGroups] = useState<Record<string, string[]>>({});
  const [selected, setSelected] = useState<string[]>([]);
  const [events, setEvents] = useState<EventRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [userName, setUserName] = useState("");
  const [savedMessage, setSavedMessage] = useState("");

  // LLM reranker state
  const [llmPrompt, setLlmPrompt] = useState("");
  const [filtering, setFiltering] = useState(false);
  const [llmMessage, setLlmMessage] = useState("");

  useEffect(() => {
    getLabels().then((res) => setGroups(res.groups));
  }, []);

  function handleToggle(label: string) {
    setSelected((prev) =>
      prev.includes(label) ? prev.filter((l) => l !== label) : [...prev, label]
    );
  }

  async function handleSearch() {
    if (selected.length === 0) return;
    setLoading(true);
    setSearched(true);
    setSavedMessage("");
    setLlmMessage("");
    try {
      const res = await getRecommendationsForLabels(selected);
      setEvents(res.recommended_events);

      // Save user if name is provided
      if (userName.trim()) {
        try {
          const saveRes = await saveNewUser(
            userName.trim(),
            selected,
            res.recommended_events
          );
          setSavedMessage(saveRes.message);
        } catch {
          setSavedMessage("Failed to save user profile");
        }
      }
    } catch {
      setEvents([]);
    }
    setLoading(false);
  }

  async function handleLLMFilter() {
    if (!llmPrompt.trim() || events.length === 0) return;
    setFiltering(true);
    setLlmMessage("");
    try {
      const res = await rerankEvents(events, llmPrompt.trim());
      setEvents(res.events);
      setLlmMessage(res.message);
    } catch {
      setLlmMessage("LLM filtering failed. Check backend logs.");
    }
    setFiltering(false);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Discover Events</h1>
        <p className="text-gray-500">
          Enter your name and select the categories you're interested in to get personalized event recommendations.
        </p>
      </div>

      {/* New User Name Input */}
      <div className="mb-6">
        <label htmlFor="userName" className="block text-sm font-medium text-gray-700 mb-1">
          Your Name
        </label>
        <input
          id="userName"
          type="text"
          placeholder="Enter your name..."
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
          className="w-full max-w-md bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-nu-purple focus:ring-1 focus:ring-nu-purple"
        />
      </div>

      <LabelSelector groups={groups} selected={selected} onToggle={handleToggle} />

      <div className="mt-6 flex items-center gap-4">
        <button
          onClick={handleSearch}
          disabled={selected.length === 0 || loading}
          className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
            selected.length === 0 || loading
              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
              : "bg-nu-purple text-white hover:bg-nu-purple-dark"
          }`}
        >
          {loading ? "Searching..." : "Get Recommendations"}
        </button>
        {selected.length > 0 && (
          <span className="text-gray-500 text-sm">
            {selected.length} label{selected.length !== 1 && "s"} selected
          </span>
        )}
      </div>

      {savedMessage && (
        <p className="mt-2 text-sm text-green-600">{savedMessage}</p>
      )}

      {/* LLM Reranker — enabled after initial search */}
      {searched && events.length > 0 && (
        <div className="mt-4">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder='Refine with AI (e.g. "only outdoor events", "events after 8pm")...'
              value={llmPrompt}
              onChange={(e) => setLlmPrompt(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLLMFilter()}
              disabled={filtering}
              className="flex-1 bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-nu-purple focus:ring-1 focus:ring-nu-purple disabled:opacity-50"
            />
            <button
              onClick={handleLLMFilter}
              disabled={filtering || !llmPrompt.trim()}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filtering || !llmPrompt.trim()
                  ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                  : "bg-nu-purple text-white hover:bg-nu-purple-dark"
              }`}
            >
              {filtering ? "Filtering..." : "Filter"}
            </button>
          </div>
          {llmMessage && (
            <p className="mt-1 text-xs text-gray-500">{llmMessage}</p>
          )}
        </div>
      )}

      {searched && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recommended Events ({events.length})
          </h2>
          <EventList events={events} />
        </div>
      )}
    </div>
  );
}

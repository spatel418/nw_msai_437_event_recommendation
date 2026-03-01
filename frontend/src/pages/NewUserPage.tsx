import { useEffect, useState } from "react";
import { getLabels, getRecommendationsForLabels } from "../api/client";
import EventList from "../components/EventList";
import LabelSelector from "../components/LabelSelector";
import type { EventRecommendation } from "../types";

export default function NewUserPage() {
  const [groups, setGroups] = useState<Record<string, string[]>>({});
  const [selected, setSelected] = useState<string[]>([]);
  const [events, setEvents] = useState<EventRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

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
    try {
      const res = await getRecommendationsForLabels(selected);
      setEvents(res.recommended_events);
    } catch {
      setEvents([]);
    }
    setLoading(false);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Discover Events</h1>
        <p className="text-gray-400">
          Select the categories you're interested in and we'll find events for you.
        </p>
      </div>

      <LabelSelector groups={groups} selected={selected} onToggle={handleToggle} />

      <div className="mt-6 flex items-center gap-4">
        <button
          onClick={handleSearch}
          disabled={selected.length === 0 || loading}
          className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
            selected.length === 0 || loading
              ? "bg-gray-600 text-gray-400 cursor-not-allowed"
              : "bg-indigo-600 text-white hover:bg-indigo-700"
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

      {/* Future LLM filter placeholder */}
      <div className="mt-4 opacity-50">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Refine with AI (coming soon)..."
            disabled
            className="flex-1 bg-gray-800 border border-gray-700 text-gray-500 rounded-lg px-4 py-2 text-sm cursor-not-allowed"
          />
          <button
            disabled
            className="bg-gray-700 text-gray-500 px-4 py-2 rounded-lg text-sm cursor-not-allowed"
          >
            Filter
          </button>
        </div>
      </div>

      {searched && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-white mb-4">
            Recommended Events ({events.length})
          </h2>
          <EventList events={events} />
        </div>
      )}
    </div>
  );
}

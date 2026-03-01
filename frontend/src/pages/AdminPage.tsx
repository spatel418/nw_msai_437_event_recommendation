import { useEffect, useState } from "react";
import {
  generateCollection,
  getCollections,
  getLabels,
  getUserRecommendations,
  rerankEvents,
} from "../api/client";
import EventList from "../components/EventList";
import LabelSelector from "../components/LabelSelector";
import PipelineStatus from "../components/PipelineStatus";
import UserDropdown from "../components/UserDropdown";
import type { Collection, EventRecommendation } from "../types";

function parseLabels(labelsStr: string): string[] {
  try {
    return JSON.parse(labelsStr.replace(/'/g, '"'));
  } catch {
    return [];
  }
}

export default function AdminPage() {
  const [selectedUser, setSelectedUser] = useState("");
  const [events, setEvents] = useState<EventRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Label filter state
  const [labelGroups, setLabelGroups] = useState<Record<string, string[]>>({});
  const [filterLabels, setFilterLabels] = useState<string[]>([]);

  // Collection state
  const [collections, setCollections] = useState<Collection[]>([]);
  const [activeCollection, setActiveCollection] = useState<string | null>(null);

  // LLM collection generator
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [collectionPrompt, setCollectionPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [createError, setCreateError] = useState("");

  // LLM reranker state
  const [llmPrompt, setLlmPrompt] = useState("");
  const [filtering, setFiltering] = useState(false);
  const [llmMessage, setLlmMessage] = useState("");

  // Load labels and collections on mount
  useEffect(() => {
    getLabels().then((res) => setLabelGroups(res.groups));
    loadCollections();
  }, []);

  async function loadCollections() {
    try {
      const res = await getCollections();
      setCollections(res.collections);
    } catch {
      // ignore
    }
  }

  async function handleUserSelect(userId: string) {
    setSelectedUser(userId);
    setError("");
    setLoading(true);
    setFilterLabels([]);
    setActiveCollection(null);
    setLlmMessage("");
    try {
      const res = await getUserRecommendations(userId);
      setEvents(res.recommended_events);
    } catch (e) {
      setEvents([]);
      setError(e instanceof Error ? e.message : "Failed to load recommendations");
    }
    setLoading(false);
  }

  function handleFilterToggle(label: string) {
    setActiveCollection(null);
    setFilterLabels((prev) =>
      prev.includes(label) ? prev.filter((l) => l !== label) : [...prev, label]
    );
  }

  function handleCollectionClick(collection: Collection) {
    if (activeCollection === collection.name) {
      setActiveCollection(null);
      setFilterLabels([]);
    } else {
      setActiveCollection(collection.name);
      setFilterLabels(collection.labels);
    }
  }

  async function handleGenerateCollection() {
    if (!collectionPrompt.trim()) return;
    setGenerating(true);
    setCreateError("");
    try {
      const res = await generateCollection(collectionPrompt.trim());
      await loadCollections();
      setCollectionPrompt("");
      setShowCreateForm(false);
      // Auto-activate the new collection
      setActiveCollection(res.collection.name);
      setFilterLabels(res.collection.labels);
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : "Failed to generate collection");
    }
    setGenerating(false);
  }

  async function handleLLMFilter() {
    if (!llmPrompt.trim() || filteredEvents.length === 0) return;
    setFiltering(true);
    setLlmMessage("");
    try {
      const res = await rerankEvents(filteredEvents, llmPrompt.trim());
      setEvents(res.events);
      setFilterLabels([]);
      setActiveCollection(null);
      setLlmMessage(res.message);
    } catch {
      setLlmMessage("LLM filtering failed. Check backend logs.");
    }
    setFiltering(false);
  }

  // Apply client-side label filtering
  const filteredEvents =
    filterLabels.length === 0
      ? events
      : events.filter((e) => {
          const eventLabels = parseLabels(e.yelp_labels);
          return filterLabels.some((fl) => eventLabels.includes(fl));
        });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main content */}
        <div className="lg:col-span-3">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Admin View</h1>
          <p className="text-gray-500 mb-6">
            Search for a user to view their pre-computed event recommendations.
          </p>

          <UserDropdown onSelect={handleUserSelect} />

          {loading && (
            <div className="mt-8 text-center text-gray-400">
              Loading recommendations...
            </div>
          )}

          {error && (
            <div className="mt-4 text-red-500 text-sm">{error}</div>
          )}

          {selectedUser && !loading && events.length > 0 && (
            <>
              {/* Collection Bubbles */}
              <div className="mt-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Collections</h3>
                <div className="flex flex-wrap gap-2">
                  {collections.map((c) => (
                    <button
                      key={c.name}
                      onClick={() => handleCollectionClick(c)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all border ${
                        activeCollection === c.name
                          ? "bg-nu-purple text-white border-nu-purple shadow-md"
                          : "bg-white text-gray-700 border-gray-300 hover:border-nu-purple-light hover:text-nu-purple"
                      }`}
                    >
                      {c.name}
                    </button>
                  ))}
                  <button
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    className={`px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                      showCreateForm
                        ? "bg-nu-purple-faint text-nu-purple border-nu-purple-light"
                        : "bg-white text-gray-500 border-dashed border-gray-300 hover:border-nu-purple-light hover:text-nu-purple"
                    }`}
                  >
                    + New Collection
                  </button>
                </div>
              </div>

              {/* LLM-Powered Collection Creator */}
              {showCreateForm && (
                <div className="mt-4 p-4 bg-nu-purple-faint border border-nu-purple-light rounded-lg">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">
                    Describe a vibe and AI will create a collection
                  </h4>
                  <p className="text-xs text-gray-500 mb-3">
                    e.g. "when I hate what's going on in the world", "perfect Sunday morning", "impressing a first date"
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Describe the mood or vibe..."
                      value={collectionPrompt}
                      onChange={(e) => setCollectionPrompt(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleGenerateCollection()}
                      disabled={generating}
                      className="flex-1 bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-nu-purple focus:ring-1 focus:ring-nu-purple disabled:opacity-50"
                    />
                    <button
                      onClick={handleGenerateCollection}
                      disabled={generating || !collectionPrompt.trim()}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        generating || !collectionPrompt.trim()
                          ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                          : "bg-nu-purple text-white hover:bg-nu-purple-dark"
                      }`}
                    >
                      {generating ? "Generating..." : "Create"}
                    </button>
                    <button
                      onClick={() => {
                        setShowCreateForm(false);
                        setCollectionPrompt("");
                        setCreateError("");
                      }}
                      className="px-3 py-2 text-sm text-gray-400 hover:text-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                  {createError && (
                    <p className="mt-2 text-red-500 text-xs">{createError}</p>
                  )}
                </div>
              )}

              {/* Label Filter Chips */}
              <div className="mt-4">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-sm font-semibold text-gray-700">Filter by Label</h3>
                  {filterLabels.length > 0 && (
                    <button
                      onClick={() => {
                        setFilterLabels([]);
                        setActiveCollection(null);
                      }}
                      className="text-xs text-nu-purple hover:text-nu-purple-dark"
                    >
                      Clear filters ({filterLabels.length})
                    </button>
                  )}
                </div>
                <LabelSelector
                  groups={labelGroups}
                  selected={filterLabels}
                  onToggle={handleFilterToggle}
                />
              </div>

              {/* LLM Reranker */}
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

              {/* Results */}
              <div className="mt-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Recommendations for{" "}
                  <span className="text-nu-purple">{selectedUser}</span>
                  {" "}({filteredEvents.length}
                  {filterLabels.length > 0 && ` of ${events.length}`} events)
                </h2>
                <EventList events={filteredEvents} showVenueInfo />
              </div>
            </>
          )}

          {selectedUser && !loading && events.length === 0 && !error && (
            <div className="mt-8 text-center text-gray-400">
              No recommendations found for this user.
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <PipelineStatus />
        </div>
      </div>
    </div>
  );
}

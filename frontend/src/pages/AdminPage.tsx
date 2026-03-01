import { useState } from "react";
import { getUserRecommendations } from "../api/client";
import EventList from "../components/EventList";
import PipelineStatus from "../components/PipelineStatus";
import UserDropdown from "../components/UserDropdown";
import type { EventRecommendation } from "../types";

export default function AdminPage() {
  const [selectedUser, setSelectedUser] = useState("");
  const [events, setEvents] = useState<EventRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleUserSelect(userId: string) {
    setSelectedUser(userId);
    setError("");
    setLoading(true);
    try {
      const res = await getUserRecommendations(userId);
      setEvents(res.recommended_events);
    } catch (e) {
      setEvents([]);
      setError(e instanceof Error ? e.message : "Failed to load recommendations");
    }
    setLoading(false);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main content */}
        <div className="lg:col-span-3">
          <h1 className="text-2xl font-bold text-white mb-2">Admin View</h1>
          <p className="text-gray-400 mb-6">
            Search for a user to view their pre-computed event recommendations.
          </p>

          <UserDropdown onSelect={handleUserSelect} />

          {loading && (
            <div className="mt-8 text-center text-gray-500">
              Loading recommendations...
            </div>
          )}

          {error && (
            <div className="mt-4 text-red-400 text-sm">{error}</div>
          )}

          {selectedUser && !loading && (
            <div className="mt-8">
              <h2 className="text-lg font-semibold text-white mb-4">
                Recommendations for{" "}
                <span className="text-indigo-400">{selectedUser}</span>
                {" "}({events.length} events)
              </h2>
              <EventList events={events} showVenueInfo />
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

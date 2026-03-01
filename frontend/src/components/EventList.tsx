import type { EventRecommendation } from "../types";
import EventCard from "./EventCard";

interface Props {
  events: EventRecommendation[];
  showVenueInfo?: boolean;
}

export default function EventList({ events, showVenueInfo = false }: Props) {
  if (events.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        No events found. Try selecting different labels.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {events.map((event) => (
        <EventCard
          key={event.event_id}
          event={event}
          showVenueInfo={showVenueInfo}
        />
      ))}
    </div>
  );
}

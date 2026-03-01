import type { EventRecommendation } from "../types";

function parseLabels(labelsStr: string): string[] {
  try {
    // Handle "['Bars', 'Nightlife']" format
    return JSON.parse(labelsStr.replace(/'/g, '"'));
  } catch {
    return [];
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "Date TBA";
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

interface Props {
  event: EventRecommendation;
  showVenueInfo?: boolean;
}

export default function EventCard({ event, showVenueInfo = false }: Props) {
  const labels = parseLabels(event.yelp_labels);
  const matchPercent = Math.round(event.score * 100);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:border-nu-purple-light hover:shadow-md transition-all">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-gray-900 font-semibold text-sm leading-tight flex-1">
          <a
            href={event.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-nu-purple transition-colors"
          >
            {event.event_name}
          </a>
        </h3>
        <span className="shrink-0 bg-nu-purple text-white text-xs font-bold px-2 py-1 rounded">
          {matchPercent}%
        </span>
      </div>

      <p className="text-gray-500 text-xs mt-1">
        {formatDate(event.start_date)}
        {event.venue_name && ` · ${event.venue_name}`}
        {event.venue_city && `, ${event.venue_city}`}
        {!event.venue_name && !event.venue_city && " · Online / TBA"}
      </p>

      <div className="flex flex-wrap gap-1 mt-2">
        {labels.map((label) => (
          <span
            key={label}
            className="bg-nu-purple-faint text-nu-purple text-xs px-2 py-0.5 rounded-full"
          >
            {label}
          </span>
        ))}
      </div>

      {showVenueInfo && event.venue_profile && (
        <div className="mt-2 pt-2 border-t border-gray-200">
          <p className="text-gray-400 text-xs">
            Matched via: <span className="text-gray-600">{event.venue_profile}</span>
          </p>
        </div>
      )}
    </div>
  );
}

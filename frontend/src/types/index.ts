export interface EventRecommendation {
  event_id: string;
  event_name: string;
  event_categories: string;
  yelp_labels: string;
  venue_name: string;
  venue_city: string;
  start_date: string;
  url: string;
  score: number;
  matched_via_venue?: string;
  venue_profile?: string;
  venue_rank?: number;
  venue_cosine_similarity?: number;
}

export interface PipelineStatus {
  is_running: boolean;
  stage: string;
  last_updated: string | null;
  last_error: string | null;
}

export interface LabelsResponse {
  labels: string[];
  groups: Record<string, string[]>;
}

export interface UserListResponse {
  users: { user_id: string }[];
  total: number;
}

export interface UserRecommendationsResponse {
  user_id: string;
  recommended_events: EventRecommendation[];
}

export interface Collection {
  name: string;
  labels: string[];
  is_default: boolean;
}

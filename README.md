# Event Recommendation System

A full-stack web application that recommends Eventbrite events to users based on their Yelp business preferences. The system bridges two domains — Yelp venue categories and Eventbrite event descriptions — using sentence embeddings, collaborative filtering, and zero-shot text classification.

## How It Works

The recommendation pipeline has two paths depending on the user type:

### Existing Users (Collaborative Filtering → Embedding Similarity)

```
User → Collaborative Filtering (matrix factorization on Yelp reviews)
     → Top 10 Yelp Venues (ranked by CF cosine similarity)
     → Each venue's categories encoded with sentence-transformer
     → Cosine similarity vs event embeddings
     → Top 1 event per venue → 10 recommended events
```

### New Users (Label Selection → Embedding Similarity)

```
User selects interest labels (e.g., "Nightlife", "Bars", "Music Venues")
     → Labels encoded as "Categories: Nightlife, Bars, Music Venues"
     → Same sentence-transformer encodes the text
     → Cosine similarity vs event embeddings
     → Top N recommended events
```

### Event Classification

Eventbrite events don't use Yelp's category taxonomy. To bridge this gap, a zero-shot classifier (`facebook/bart-large-mnli`) re-tags each scraped event with Yelp-style labels from a curated set of 35 categories. This puts events and venues in the same semantic space for embedding comparison.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (React + Vite + TypeScript + Tailwind) │
│  ┌──────────────┐  ┌───────────────────────────┐ │
│  │ New User View│  │ Admin View                │ │
│  │ Pick labels  │  │ Search users, view recs   │ │
│  │ See events   │  │ Update Events pipeline    │ │
│  └──────────────┘  └───────────────────────────┘ │
└──────────────────────┬──────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────┐
│  Backend (FastAPI)                               │
│  ┌─────────────┐ ┌────────────┐ ┌─────────────┐ │
│  │ /api/admin  │ │/api/recommend│ │/api/pipeline│ │
│  │ User lookup │ │ Label→events │ │ Update flow │ │
│  └─────────────┘ └────────────┘ └─────────────┘ │
│                                                  │
│  Services:                                       │
│  - embedding_service (all-mpnet-base-v2)         │
│  - classifier_service (bart-large-mnli)          │
│  - scraper_service (Eventbrite)                  │
│  - recommendation_service (venue→event mapping)  │
│  - pipeline_service (orchestrates full update)   │
│  - llm_service (Azure OpenAI reranker scaffold)  │
└──────────────────────────────────────────────────┘
```

## Project Structure

```
nw_msai_437_event_recommendation/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # All paths, constants, model names
│   ├── state.py                # In-memory app state singleton
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── data_loader.py      # Loads JSON/CSV/NPY on startup
│   │   ├── embedding_service.py    # Sentence-transformer encode + similarity
│   │   ├── scraper_service.py      # Eventbrite web scraping
│   │   ├── classifier_service.py   # BART zero-shot classification
│   │   ├── recommendation_service.py  # Venue→event + user→event logic
│   │   ├── pipeline_service.py     # Full update pipeline orchestrator
│   │   └── llm_service.py         # Azure OpenAI reranker (scaffold)
│   └── routers/
│       ├── admin.py            # User list + user recommendations
│       ├── new_user.py         # Label selection + event matching
│       ├── pipeline.py         # Trigger + status for background update
│       └── llm.py              # LLM reranker endpoint (scaffold)
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Router: / → NewUser, /admin → Admin
│   │   ├── api/client.ts       # API client for all backend calls
│   │   ├── types/index.ts      # TypeScript interfaces
│   │   ├── components/
│   │   │   ├── Navbar.tsx          # Top navigation
│   │   │   ├── LabelSelector.tsx   # Selectable category chips
│   │   │   ├── EventCard.tsx       # Event recommendation card
│   │   │   ├── EventList.tsx       # Grid of event cards
│   │   │   ├── UserDropdown.tsx    # Searchable user dropdown
│   │   │   └── PipelineStatus.tsx  # Pipeline status + update button
│   │   └── pages/
│   │       ├── NewUserPage.tsx     # Discover events flow
│   │       └── AdminPage.tsx       # Admin dashboard
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── data/                       # All data artifacts
│   ├── illinois_business_mapping.json     # 2,106 Yelp venues
│   ├── illinois_user_recommendations.json # ~3,953 users (CF output)
│   ├── chicago_eventbrite_scraped.csv     # Scraped + classified events
│   ├── event_embeddings_v3.npy            # Event embeddings (N, 768)
│   ├── venue_embeddings_v3.npy            # Venue embeddings (N, 768)
│   ├── events_with_text_v3.csv            # Events with text + labels
│   ├── venues_with_text_v3.csv            # Venues with category text
│   ├── venue_event_map_v3.json            # Venue → top events mapping
│   └── user_event_recommendations_v3.json # User → recommended events
├── notebooks/                  # Original Jupyter notebooks
├── legacy/                     # Archived v1/v2/v3 scripts
└── pyproject.toml
```

## Prerequisites

- **Python 3.12+**
- **Poetry** (Python dependency manager)
- **Node.js 18+** (for the frontend)
- **Yarn** or **npm** (package manager)

## Setup

### 1. Python Environment

```bash
poetry install
```

This installs all Python dependencies from `pyproject.toml` into a Poetry-managed virtual environment. To add the backend-specific dependencies (if not already in pyproject.toml):

```bash
poetry add fastapi uvicorn transformers torch requests beautifulsoup4
```

### 2. Frontend Dependencies

```bash
cd frontend
yarn install
```

### 3. Data Files

All files in `data/` are included in the repo so the app works immediately after cloning. The "Update Events" button in the admin view can refresh the event data with the latest Eventbrite listings at any time.

## Running the Application

### Start the Backend

```bash
# From the project root
poetry run uvicorn backend.main:app --reload --port 8000
```

On startup, the server:
1. Loads all data files into memory (~30MB)
2. Loads the sentence-transformer model (`all-mpnet-base-v2`, ~420MB)
3. Serves the API at `http://localhost:8000`
4. Swagger docs available at `http://localhost:8000/docs`

### Start the Frontend

```bash
cd frontend
yarn dev
```

Opens at `http://localhost:5173`. The Vite dev server proxies all `/api` requests to the backend at `localhost:8000`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check with loaded data counts |
| GET | `/api/recommend/labels` | Returns 35 Yelp-style labels grouped by category |
| POST | `/api/recommend/events` | New user: selected labels → event recommendations |
| GET | `/api/admin/users` | List user IDs (with search, pagination) |
| GET | `/api/admin/users/{id}/recommendations` | Get a user's pre-computed recommendations |
| POST | `/api/pipeline/update` | Trigger background event update pipeline |
| GET | `/api/pipeline/status` | Check pipeline progress |
| POST | `/api/llm/rerank` | LLM reranker (scaffold — returns events unchanged) |

## Update Events Pipeline

The admin view has an "Update Events" button that triggers a background pipeline:

1. **Scrape** — Crawls ~25 pages of Eventbrite Chicago search results (~500 events, ~15 min)
2. **Classify** — Loads `facebook/bart-large-mnli` and classifies each event with 35 Yelp-style labels using zero-shot classification (threshold: 0.30)
3. **Embed** — Encodes event text with `all-mpnet-base-v2` sentence-transformer
4. **Recommend** — Rebuilds venue→event map and user→event recommendations
5. **Cleanup** — Unloads BART model to free memory

Total runtime: ~20-30 minutes. The frontend polls for status every 60 seconds while running.

## Models Used

| Model | Size | Purpose | When Loaded |
|-------|------|---------|-------------|
| `all-mpnet-base-v2` | ~420MB | Sentence embeddings for venues, events, and new user queries | Server startup (stays resident) |
| `facebook/bart-large-mnli` | ~1.6GB | Zero-shot event classification into Yelp categories | Only during "Update Events" pipeline (unloaded after) |

## Hardware Notes

Tested on a machine with a GTX 1650 (4GB VRAM). The sentence-transformer runs on GPU if available. BART runs on CPU by default to avoid VRAM contention. Both models can fit on GPU simultaneously (~2GB total) if needed.

## Future Work

- **Azure OpenAI LLM reranker** — The `/api/llm/rerank` endpoint is scaffolded. Once an Azure OpenAI resource is provisioned, it will allow users to filter recommendations with natural language prompts (e.g., "only events after 8pm", "prefer outdoor events").

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import admin, llm, new_user, pipeline
from backend.services import data_loader, embedding_service
from backend.state import app_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    data_loader.load_all(app_state)
    embedding_service.load_model()
    yield
    # --- SHUTDOWN ---
    print("Shutting down.")


app = FastAPI(
    title="Event Recommender",
    description="Recommend Eventbrite events based on Yelp user preferences",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(new_user.router, prefix="/api/recommend", tags=["recommend"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "users_loaded": len(app_state.user_ids),
        "events_loaded": len(app_state.events_df) if app_state.events_df is not None else 0,
    }

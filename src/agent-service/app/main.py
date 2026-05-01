from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Agentic SDLC Agent Service",
    version="0.1.0",
    description="LangGraph-backed workflow and agent execution service.",
)

app.include_router(router)


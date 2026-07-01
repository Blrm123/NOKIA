"""
app/api/router.py
------------------
Central API router — registers all sub-routers.

Responsibilities:
- Import each feature router
- Attach them to the main APIRouter with appropriate prefixes / tags
- Nothing else; no business logic, no middleware
"""

from fastapi import APIRouter

from app.api import health, webhook

# Main router that is registered on the FastAPI app in main.py
api_router = APIRouter()

# Health check — no prefix so the endpoint is at /health
api_router.include_router(health.router)

# GitHub webhook — no additional prefix; endpoint is at /webhook/github
api_router.include_router(webhook.router)

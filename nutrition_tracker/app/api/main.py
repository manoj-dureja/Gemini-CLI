from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import logging, dishes, analytics

app = FastAPI(
    title="Bespoke Nutrition Tracker API",
    description="Backend for high-precision food logging and analytics.",
    version="1.0.0"
)

# Set up CORS for the Streamlit/React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(logging.router, prefix="/api/v1", tags=["Logging"])
app.include_router(dishes.router, prefix="/api/v1", tags=["Dishes"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

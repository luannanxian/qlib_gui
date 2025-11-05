"""
FastAPI main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.user_onboarding.api import mode_api
from app.modules.data_management.api import dataset_api

app = FastAPI(
    title="Qlib-UI API",
    description="Quantitative Investment Research Platform API",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(mode_api.router, prefix="/api/user", tags=["user"])
app.include_router(dataset_api.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Qlib-UI API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

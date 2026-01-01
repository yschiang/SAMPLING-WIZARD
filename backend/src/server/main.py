from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import catalog, sampling, recipes

app = FastAPI(
    title="Sampling Wizard API (Prototype v0)",
    version="0.1.0",
    description="API contract for Sampling & Recipe Generation Wizard",
    servers=[{"url": "http://localhost:8080"}],
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(catalog.router, prefix="/v1/catalog", tags=["catalog"])
app.include_router(sampling.router, prefix="/v1/sampling", tags=["sampling"])
app.include_router(recipes.router, prefix="/v1/recipes", tags=["recipes"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
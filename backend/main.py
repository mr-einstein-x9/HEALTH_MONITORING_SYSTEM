from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth_router, health_router, dashboard_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Health Monitoring System API",
    description="Backend system for a Software-Based Health Monitoring System.",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(dashboard_router)

@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Health Monitoring System API. Go to /docs for the interactive API documentation."}

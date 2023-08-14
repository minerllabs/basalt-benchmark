from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from api import api_router
from database import engine
from models import Base
from frontend import frontend_router

########################################################################
# Database Instantiation
########################################################################
Base.metadata.create_all(bind=engine)


########################################################################
# App Instantiation
########################################################################
app = FastAPI(
    title="BASALT Human Evaluation Interface",
    description="Interface for human evaluation of episode videos of submitted agents",
)

# CORS allow all
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files route
app.mount("/static", StaticFiles(directory="static"), name="static")

# Backend API routes
app.include_router(api_router)

# Frontend routes
app.include_router(frontend_router)


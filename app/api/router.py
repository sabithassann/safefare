from fastapi import APIRouter
from app.api.endpoints import users, fares, ai_assistant, charts

api_router = APIRouter()
api_router.include_router(fares.router, prefix="/fares", tags=["Fares"])
api_router.include_router(charts.router, prefix="/charts", tags=["Charts"])
api_router.include_router(ai_assistant.router, prefix="/ai", tags=["AI Assistant"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

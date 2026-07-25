from fastapi import APIRouter
from app.schemas.fare import AIRequest, AIResponse
from app.services.ai_service import generate_ai_response

router = APIRouter()

@router.post("/ask", response_model=AIResponse)
def ask_ai(request: AIRequest):
    """
    Ask the SafeFare AI assistant a question regarding fares or routes.
    """
    answer = generate_ai_response(request.question, request.context_route)
    return AIResponse(answer=answer)

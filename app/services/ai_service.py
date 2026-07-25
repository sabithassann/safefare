def generate_ai_response(question: str, context_route: str = None) -> str:
    """
    Mock AI Service to answer user queries about fares and routes.
    Eventually connect to OpenAI/Local LLM.
    """
    question_lower = question.lower()
    
    # Simple hardcoded mock logic for demonstration
    if "vara koto" in question_lower or "fare" in question_lower:
        return "Sir, the fare depends on your source and destination. Please use the search bar to find the exact BTRC approved fare."
    
    if "route" in question_lower:
        return "We have data for multiple city bus routes. Where do you want to go?"

    return "I am the SafeFare AI Assistant. I can help you with bus routes and government approved fares. How can I help you today?"

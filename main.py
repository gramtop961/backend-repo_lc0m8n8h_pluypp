import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from schemas import ChatRequest, ChatResponse, PlanRequest, PlanResponse, Generation
from database import create_document, db

app = FastAPI(title="AI Builder Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ------------------- AI Endpoints -------------------

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Lightweight heuristic chatbot to keep the demo self-contained."""
    user_msg = (req.message or "").strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Simple intent-based responses
    lower = user_msg.lower()
    if any(k in lower for k in ["hello", "hi", "hey"]):
        reply = "Hey! I'm your AI builder. Tell me what you want to create."
    elif any(k in lower for k in ["website", "app", "build", "create"]):
        reply = (
            "Great! Share your idea, target audience, and key features. "
            "I can draft a plan and spin up a starter in minutes."
        )
    elif any(k in lower for k in ["pricing", "cost", "price"]):
        reply = "This demo is free. In production, cost depends on features and integrations."
    else:
        reply = (
            "Got it. I can help you plan features, pages, and backend endpoints. "
            "Use the planner below to generate a build plan."
        )

    # Optionally echo last hint based on history
    if req.history and len(req.history) > 0:
        last_user = next((m.content for m in reversed(req.history) if m.role == "user"), None)
        if last_user and last_user != user_msg and len(last_user) < 120:
            reply += f" Also noted: '{last_user}'."

    return ChatResponse(reply=reply)

@app.post("/api/plan", response_model=PlanResponse)
def plan_endpoint(req: PlanRequest):
    idea = (req.idea or "").strip()
    if not idea:
        raise HTTPException(status_code=400, detail="Idea is required")

    features = req.features or []

    # Draft a starter implementation plan
    plan = {
        "summary": f"Plan to build: {idea}",
        "frontend": {
            "stack": ["Vite + React", "TailwindCSS", "Lucide Icons", "Framer Motion"],
            "pages": ["Home/Hero with 3D Spline", "Features", "Chatbot", "Dashboard (optional)"],
            "components": ["Navbar", "Hero", "Chatbot", "Planner", "Footer"],
            "api_usage": ["POST /api/chat", "POST /api/plan"],
        },
        "backend": {
            "stack": ["FastAPI", "MongoDB"],
            "endpoints": [
                {"route": "/api/chat", "method": "POST", "desc": "Conversational helper"},
                {"route": "/api/plan", "method": "POST", "desc": "Generate build plan and store"},
            ],
            "collections": ["generation"],
        },
        "features": features,
        "next_steps": [
            "Review and tweak the plan",
            "Auto-generate starter components",
            "Iterate with the chatbot for refinements",
        ],
    }

    # Persist the request
    try:
        gen = Generation(idea=idea, features=features, status="planned", plan=plan)
        inserted_id = create_document("generation", gen)
    except Exception as e:
        # If DB not available, still return the plan with a pseudo id
        inserted_id = "no-db"

    return PlanResponse(id=str(inserted_id), status="planned", plan=plan)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

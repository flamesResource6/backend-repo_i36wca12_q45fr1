import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

# Database helpers
from database import db, create_document, get_documents

app = FastAPI(title="LibVault API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "LibVault Backend Ready", "version": "1.0.0"}


# ---------- Utility & Schema exposure ----------
@app.get("/schema")
def get_schema_index():
    """Expose available Pydantic schema class names for the database viewer."""
    try:
        import schemas as s
        # Collect model names defined in schemas module
        models = [
            name for name, obj in s.__dict__.items()
            if isinstance(obj, type) and issubclass(obj, s.BaseModel) and name not in ("BaseModel",)
        ]
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response: Dict[str, Any] = {
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
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ---------- Auth & Security (stubs) ----------
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]

@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    # Stub: Always succeed with a demo token
    user = {"email": payload.email, "name": "Demo User", "role": "admin"}
    return {"token": "demo.jwt.token", "user": user}

class TwoFASetupResponse(BaseModel):
    secret: str
    qr_svg: str

@app.get("/api/security/2fa/setup", response_model=TwoFASetupResponse)
def twofa_setup():
    # Stub 2FA secret & QR (not real TOTP)
    return {
        "secret": "JBSWY3DPEHPK3PXP",
        "qr_svg": "<svg width='120' height='120'><rect width='120' height='120' fill='#0EA5E9'/></svg>"
    }

class TwoFAVerifyRequest(BaseModel):
    code: str

@app.post("/api/security/2fa/verify")
def twofa_verify(payload: TwoFAVerifyRequest):
    ok = payload.code == "000000"  # demo code
    return {"verified": ok}


# ---------- RBAC check (simple rule) ----------
@app.get("/api/security/rbac")
def rbac(role: str = Query("member")):
    permissions = {
        "admin": ["manage_users", "manage_books", "view_reports", "billing"],
        "librarian": ["manage_books", "transactions"],
        "member": ["borrow", "read"]
    }
    return {"role": role, "permissions": permissions.get(role, [])}


# ---------- AI Features (inference-free stubs) ----------
class SummaryRequest(BaseModel):
    text: str = Field(..., description="Input to summarize")
    max_sentences: int = 3

@app.post("/api/ai/summary")
def ai_summary(payload: SummaryRequest):
    sentences = [s.strip() for s in payload.text.replace("\n", " ").split('.') if s.strip()]
    summary = '. '.join(sentences[:payload.max_sentences]) + ('.' if sentences else '')
    return {"summary": summary, "sentences_used": min(len(sentences), payload.max_sentences)}

class AISearchRequest(BaseModel):
    query: str

@app.post("/api/ai/search")
def ai_search(payload: AISearchRequest):
    # Very basic keyword search in books collection
    try:
        results = list(db["book"].find({"$text": {"$search": payload.query}}).limit(10)) if db else []
    except Exception:
        # Fallback to regex OR search on title
        results = list(db["book"].find({"title": {"$regex": payload.query, "$options": "i"}}).limit(10)) if db else []
    # Normalize
    for r in results:
        r["_id"] = str(r["_id"])  # type: ignore
    return {"query": payload.query, "results": results}

class RecommendRequest(BaseModel):
    user_id: str

@app.post("/api/ai/recommend")
def ai_recommend(payload: RecommendRequest):
    # Rule-based: top 5 most recently added available books
    items = get_documents("book", {"available": True}, limit=5) if db else []
    for r in items:
        if "_id" in r:
            r["_id"] = str(r["_id"])  # type: ignore
    return {"user_id": payload.user_id, "recommendations": items}


# ---------- Monetization ----------
class SubscriptionRequest(BaseModel):
    user_id: str
    plan: str = Field("pro", description="free|pro|enterprise")

@app.post("/api/billing/subscriptions")
def create_subscription(payload: SubscriptionRequest):
    sub = {
        "user_id": payload.user_id,
        "plan": payload.plan,
        "status": "active",
        "renews_at": datetime.utcnow() + timedelta(days=30)
    }
    sub_id = create_document("subscription", sub)
    return {"id": sub_id, **sub}

@app.get("/api/billing/invoices")
def list_invoices(user_id: Optional[str] = None):
    filt = {"user_id": user_id} if user_id else {}
    docs = get_documents("invoice", filt, limit=50) if db else []
    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])  # type: ignore
    return {"invoices": docs}


# ---------- Community ----------
class ForumPostIn(BaseModel):
    user_id: str
    title: str
    content: str
    tags: List[str] = []

@app.post("/api/community/forums")
def create_forum_post(payload: ForumPostIn):
    post_id = create_document("forumpost", payload.dict())
    return {"id": post_id, **payload.dict()}

@app.get("/api/community/forums")
def list_forum_posts(tag: Optional[str] = None):
    filt = {"tags": tag} if tag else {}
    posts = get_documents("forumpost", filt, limit=50) if db else []
    for p in posts:
        if "_id" in p:
            p["_id"] = str(p["_id"])  # type: ignore
    return {"posts": posts}


# ---------- Backup (stub) ----------
@app.post("/api/backup/run")
def trigger_backup():
    # Stub backup status
    return {"status": "queued", "started_at": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

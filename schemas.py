"""
Database Schemas for LibVault (Library Management System)

Each Pydantic model represents a collection in MongoDB. The collection name is the lowercase
of the class name. Example: class User -> "user" collection.

These schemas power the database viewer and validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: str = Field("member", description="Role based access: admin|librarian|member")
    avatar: Optional[str] = Field(None, description="Avatar URL")
    is_active: bool = Field(True, description="Active status")
    two_factor_enabled: bool = Field(False, description="2FA enabled")

class Book(BaseModel):
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Author name")
    isbn: Optional[str] = Field(None, description="ISBN")
    category: Optional[str] = Field(None, description="Category/Genre")
    year: Optional[int] = Field(None, description="Publication year")
    summary: Optional[str] = Field(None, description="Short description")
    available: bool = Field(True, description="Availability status")
    cover_url: Optional[str] = Field(None, description="Cover image URL")
    tags: List[str] = Field(default_factory=list, description="Tags for search")

class Transaction(BaseModel):
    user_id: str = Field(..., description="Borrower user id")
    book_id: str = Field(..., description="Borrowed book id")
    type: str = Field(..., description="borrow|return|renew")
    due_date: Optional[datetime] = Field(None, description="Due date for returns")
    returned_at: Optional[datetime] = Field(None, description="Return timestamp")
    status: str = Field("open", description="open|closed|overdue")

class Invoice(BaseModel):
    user_id: str
    amount: float
    currency: str = Field("USD")
    status: str = Field("pending", description="pending|paid|failed|refunded")
    description: Optional[str] = None

class Subscription(BaseModel):
    user_id: str
    plan: str = Field("pro", description="free|pro|enterprise")
    status: str = Field("active", description="active|trial|expired|canceled")
    renews_at: Optional[datetime] = None

class ForumPost(BaseModel):
    user_id: str
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    likes: int = 0

class Club(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: str
    members: List[str] = Field(default_factory=list)

class Recommendation(BaseModel):
    user_id: str
    book_ids: List[str] = Field(default_factory=list)
    strategy: str = Field("rule-based")

# Note: The Flames database viewer will automatically read these schemas from
# GET /schema and handle CRUD operations. You can still create custom endpoints
# for AI features and business workflows.

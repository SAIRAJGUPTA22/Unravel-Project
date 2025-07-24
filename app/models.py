from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class Article(BaseModel):
    article_id: str
    url: HttpUrl
    title: str
    summary: Optional[str] = ""
    published: datetime  # Always timezone-aware!
    source: str
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

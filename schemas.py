from typing import Optional
from pydantic import BaseModel, Field

class BookBase(BaseModel):
    title: str
    author: str
    pages: int = Field(..., ge=1)
    image: Optional[str] = None
    author_image: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookOut(BookBase):
    pass

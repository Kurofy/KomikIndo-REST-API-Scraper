from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized JSON response wrapper."""
    status: str = Field(default="success", description="Response status: success or error")
    message: str = Field(default="OK", description="Human-readable message")
    base_url_used: str = Field(..., description="Active target base URL used to fetch data")
    cached: bool = Field(default=False, description="Whether this response was served from memory cache")
    data: Optional[T] = Field(default=None, description="Payload data")


class Pagination(BaseModel):
    current_page: int = 1
    has_next_page: bool = False
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
    total_pages: Optional[int] = None

"""Shared schemas for pagination, error responses, and common patterns."""

from uuid import UUID

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort: str = "created_at"
    order: str = Field("desc", pattern="^(asc|desc)$")


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int


class ErrorResponse(BaseModel):
    error: str
    code: str
    detail: str | None = None


class IDResponse(BaseModel):
    id: UUID

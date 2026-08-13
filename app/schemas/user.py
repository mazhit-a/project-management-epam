from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserCreate(BaseModel):
    login: str = Field(min_length=3, max_length=255, examples=["jdoe"])
    password: str = Field(min_length=8, max_length=128)
    password_repeat: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def _passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError("password and password_repeat do not match")
        return self


class UserRead(BaseModel):
    """Response model. Deliberately excludes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login: str
    created_at: datetime


class LoginRequest(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")

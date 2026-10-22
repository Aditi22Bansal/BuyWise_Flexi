from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class UserResponse(BaseModel):
    username: str
    name: str
    role: str
    role_label: str
    title: str
    description: str
    approval_limit: Optional[float] = None


class LoginResponse(BaseModel):
    token: str
    user: UserResponse

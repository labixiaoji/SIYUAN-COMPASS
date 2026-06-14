from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RegisterInput(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=8, max_length=128)
    displayName: str = Field(min_length=1, max_length=40)


class LoginInput(BaseModel):
    username: str
    password: str


class AuthUser(BaseModel):
    id: str
    username: str
    displayName: str
    role: Literal["student", "admin"]


class AuthResult(BaseModel):
    token: str
    user: AuthUser

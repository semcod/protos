from __future__ import annotations

from typing import List

from pydantic import BaseModel

class CreateUserCommand(BaseModel):
    email: str
    password: str

class GetUserQuery(BaseModel):
    id: str

class User(BaseModel):
    id: str
    email: str

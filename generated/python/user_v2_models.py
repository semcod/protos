from __future__ import annotations

import datetime
from enum import Enum
from typing import List, Dict

from pydantic import BaseModel

class CreateUserCommand(BaseModel):
    email: str
    first_name: str
    last_name: str

class GetUserQuery(BaseModel):
    id: str

class User(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str

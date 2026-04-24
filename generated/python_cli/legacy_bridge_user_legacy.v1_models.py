from __future__ import annotations

import datetime
from enum import Enum
from typing import List, Dict

from pydantic import BaseModel

class LegacyUser(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    age: int
    is_active: bool
    tags: list[str]

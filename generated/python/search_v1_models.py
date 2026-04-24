from __future__ import annotations

import datetime
from enum import Enum
from typing import List, Dict

from pydantic import BaseModel

class IndexEntryCommand(BaseModel):
    id: str
    title: str
    category: str
    content: str
    metadata: dict[str, str]

class EntryIndexed(BaseModel):
    id: str
    title: str
    category: str
    timestamp: float

class SearchRequest(BaseModel):
    query: str
    category_filter: str
    limit: int

class SearchResponse(BaseModel):
    results: list[Result]
    total_count: int

class Result(BaseModel):
    id: str
    title: str
    category: str
    score: float

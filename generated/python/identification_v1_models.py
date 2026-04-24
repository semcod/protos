from __future__ import annotations

import datetime
from enum import Enum
from typing import List, Dict

from pydantic import BaseModel

class IdentifierType(Enum):
    IDENTIFIER_TYPE_UNSPECIFIED = 0
    IDENTIFIER_TYPE_RFID = 1
    IDENTIFIER_TYPE_QR = 2
    IDENTIFIER_TYPE_BARCODE = 3
    IDENTIFIER_TYPE_MANUAL = 4

class IdentifyUserCommand(BaseModel):
    command_id: str
    identifier: str
    type: IdentifierType

class UserIdentificationReadModel(BaseModel):
    user_id: str
    display_name: str
    roles: list[str]
    identified_at: datetime.datetime

class UserIdentifiedEvent(BaseModel):
    event_id: str
    user_id: str
    type: IdentifierType
    occurred_at: datetime.datetime

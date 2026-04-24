"""
test_dual_write.py – tests for the dual-write pattern with idempotency.
"""

import os
import pytest
import uuid
from scripts.event_store import EventStore
from scripts.dual_writer import DualWriter, LegacyDB
from scripts.idempotency_store import IdempotencyStore

@pytest.fixture
def clean_dbs():
    paths = ["test_event_store.db", "test_legacy.db", "test_idempotency.db"]
    for p in paths:
        if os.path.exists(p):
            os.remove(p)
    
    yield paths
    
    for p in paths:
        if os.path.exists(p):
            os.remove(p)

def test_dual_write_success(clean_dbs):
    es = EventStore("test_event_store.db")
    ldb = LegacyDB("test_legacy.db")
    idem = IdempotencyStore("test_idempotency.db")
    writer = DualWriter(es, ldb, idem)

    command_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    payload = {
        "id": user_id,
        "email": "dual@test.com",
        "first_name": "Dual",
        "last_name": "Write",
        "age": 30,
        "is_active": True
    }

    # First write
    res1 = writer.execute_create_user(command_id, payload)
    assert res1["status"] == "success"
    assert res1["version"] == 1

    # Verify Event Store
    events = es.get_stream(user_id)
    assert len(events) == 1
    assert events[0].payload["email"] == "dual@test.com"

    # Verify Legacy DB
    row = ldb.conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
    assert row["email"] == "dual@test.com"


def test_idempotency_prevents_duplicate(clean_dbs):
    es = EventStore("test_event_store.db")
    ldb = LegacyDB("test_legacy.db")
    idem = IdempotencyStore("test_idempotency.db")
    writer = DualWriter(es, ldb, idem)

    command_id = "same-command-id"
    user_id = "user-1"
    payload = {"id": user_id, "email": "a@a.com", "first_name": "A", "last_name": "B", "age": 20, "is_active": True}

    # First execution
    res1 = writer.execute_create_user(command_id, payload)
    assert res1["status"] == "success"

    # Second execution with same command_id
    res2 = writer.execute_create_user(command_id, payload)
    assert res2 == res1  # Should return cached response
    
    # Verify only one event in store
    events = es.get_stream(user_id)
    assert len(events) == 1

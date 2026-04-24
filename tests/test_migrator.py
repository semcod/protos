"""
test_migrator.py – tests for bootstrapping EventStore from legacy DB.
"""

import os
import pytest
from scripts.event_store import EventStore
from scripts.dual_writer import LegacyDB
from scripts.legacy_bridge.migrator import migrate_users

@pytest.fixture
def dbs():
    l_path = "test_legacy_mig.db"
    e_path = "test_event_store_mig.db"
    for p in [l_path, e_path]:
        if os.path.exists(p): os.remove(p)
    
    yield l_path, e_path
    
    for p in [l_path, e_path]:
        if os.path.exists(p): os.remove(p)

def test_migration_bootstrap(dbs):
    l_path, e_path = dbs
    ldb = LegacyDB(l_path)
    es = EventStore(e_path)

    # 1. Seed legacy data
    users = [
        {"id": "u1", "email": "u1@test.com", "first_name": "U1", "last_name": "T", "age": 20, "is_active": True},
        {"id": "u2", "email": "u2@test.com", "first_name": "U2", "last_name": "T", "age": 25, "is_active": True},
    ]
    for u in users:
        ldb.upsert_user(u)

    # 2. Run migration
    count = migrate_users(ldb, es)
    assert count == 2

    # 3. Verify EventStore
    events_u1 = es.get_stream("u1")
    assert len(events_u1) == 1
    assert events_u1[0].event_type == "UserCreated"
    assert events_u1[0].payload["email"] == "u1@test.com"

    # 4. Run migration again (should skip)
    count2 = migrate_users(ldb, es)
    assert count2 == 0

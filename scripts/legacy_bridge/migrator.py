"""
migrator.py – bootstrap EventStore from legacy database data.
This script performs a one-time migration of historical state.
"""

from __future__ import annotations
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from event_store import EventStore
from dual_writer import LegacyDB

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def migrate_users(legacy_db: LegacyDB, event_store: EventStore) -> int:
    """
    Reads all users from legacy DB and appends UserCreated events to EventStore.
    Returns the count of migrated users.
    """
    users = legacy_db.get_all_users()
    count = 0

    for user in users:
        # Check if user already has events to avoid duplicates
        existing = event_store.get_stream(user["id"])
        if existing:
            log.info("User %s already has events. Skipping.", user["id"])
            continue

        # Convert legacy user to event payload
        # Note: We use version=0 to indicate this is a fresh append (optimistic CC)
        event_store.append(
            aggregate_id=user["id"],
            event_type="UserCreated",
            payload={
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "age": user["age"],
                "is_active": bool(user["is_active"])
            }
        )
        log.info("Migrated user %s (%s)", user["id"], user["email"])
        count += 1

    return count


def main() -> None:
    # Use default paths or env vars
    legacy_path = os.getenv("LEGACY_DB_PATH", "legacy.db")
    event_store_path = os.getenv("EVENT_STORE_PATH", "event_store.db")

    log.info("Starting migration from %s to %s", legacy_path, event_store_path)

    ldb = LegacyDB(legacy_path)
    es = EventStore(event_store_path)

    count = migrate_users(ldb, es)
    log.info("Migration complete. %d users migrated.", count)


if __name__ == "__main__":
    main()

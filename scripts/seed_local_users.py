#!/usr/bin/env python3
"""Idempotent seed for local development users.

Requires LOCAL_DEV_PASSWORD in the environment. See README for the dev-only
password convention; never commit real credentials.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal, init_db_connection  # noqa: E402
from app.models.user import User, UserRole, UserStatus  # noqa: E402

SEED_USERS: tuple[tuple[str, str, UserRole], ...] = (
    ("analyst@local.dev", "Local Analyst", UserRole.analyst),
    ("admin@local.dev", "Local Admin", UserRole.admin),
)


def seed_local_users() -> int:
    """Create or update the default local dev users."""
    password = os.environ.get("LOCAL_DEV_PASSWORD")
    if not password:
        print(
            "LOCAL_DEV_PASSWORD is required. Set it in your shell (see README).",
            file=sys.stderr,
        )
        return 1

    init_db_connection()
    assert SessionLocal is not None
    password_hash = hash_password(password)
    created = 0
    updated = 0

    with SessionLocal() as db:
        for email, display_name, role in SEED_USERS:
            existing = db.scalar(select(User).where(User.email == email))
            if existing is None:
                db.add(
                    User(
                        email=email,
                        display_name=display_name,
                        password_hash=password_hash,
                        role=role,
                        status=UserStatus.active,
                    )
                )
                created += 1
                continue

            existing.display_name = display_name
            existing.password_hash = password_hash
            existing.role = role
            existing.status = UserStatus.active
            updated += 1

        db.commit()

    print(f"Seed complete: created={created}, updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(seed_local_users())

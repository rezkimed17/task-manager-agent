from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Base, User, UserSettings
from app.security import hash_password


def main():
    settings = get_settings()
    os.makedirs("data", exist_ok=True)
    engine = create_engine(settings.sync_database_url, future=True)
    Base.metadata.bind = engine
    with Session(engine) as db:
        exists = db.query(User).filter(User.email == settings.initial_admin_email).first()
        if not exists:
            u = User(email=settings.initial_admin_email, password_hash=hash_password(settings.initial_admin_password))
            db.add(u)
            db.flush()
            us = UserSettings(
                user_id=u.id,
                default_tz=settings.default_tz,
                work_hours_start=settings.work_hours_start,
                work_hours_end=settings.work_hours_end,
            )
            db.add(us)
            db.commit()
            print(f"Seeded user {settings.initial_admin_email}")
        else:
            print("User exists; skipping")


if __name__ == "__main__":
    main()


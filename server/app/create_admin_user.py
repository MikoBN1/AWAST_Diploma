"""
Create an admin user in the database.

Run from the app directory so `.env` is picked up by settings:

    cd server/app
    python create_admin_user.py --email admin@example.com --password 'your-secret'

You can also set ADMIN_EMAIL, ADMIN_USERNAME, and ADMIN_PASSWORD in the environment
and omit the corresponding CLI flags.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from models.users_model import User
from services.database_service import AsyncDatabaseService
from utils.auth_util import hash_password
from core.database import async_session, engine

database_service = AsyncDatabaseService(async_session)


async def create_admin(*, email: str, username: str, password: str) -> None:
    existing = await database_service.get(User, email=email)
    if existing:
        print(f"User with email {email!r} already exists.", file=sys.stderr)
        sys.exit(1)

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="admin",
        enabled_domains=[],
    )
    await database_service.create(user)
    print(f"Admin user created: {email!r} (username={username!r}).")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--email",
        default=os.getenv("ADMIN_EMAIL"),
        help="Admin email (default: env ADMIN_EMAIL)",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("ADMIN_USERNAME"),
        help="Display name (default: local part of email, or env ADMIN_USERNAME)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("ADMIN_PASSWORD"),
        help="Plain password (default: env ADMIN_PASSWORD)",
    )
    return parser.parse_args()


async def main() -> None:
    args = _parse_args()
    if not args.email:
        print("Missing --email or ADMIN_EMAIL.", file=sys.stderr)
        sys.exit(2)
    if not args.password:
        print("Missing --password or ADMIN_PASSWORD.", file=sys.stderr)
        sys.exit(2)
    username = args.username or args.email.split("@", 1)[0]

    try:
        await create_admin(email=args.email, username=username, password=args.password)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

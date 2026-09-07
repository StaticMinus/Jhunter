"""
AI Job Hunter — Manual OAuth Code Exchange Utility
Use this script if a remote candidate (like Andrew) authorizes Google OAuth on their
own machine and sends you the redirect URL or the authorization code.

Usage:
    python scripts/exchange_oauth_code.py --url "http://localhost:8000/api/auth/google/callback?code=4/0A...&state=andrewchukwuka90%40gmail.com"
    OR
    python scripts/exchange_oauth_code.py --email andrewchukwuka90@gmail.com --code "4/0A..."
"""

import os
import sys
import json
import asyncio
import urllib.parse
import argparse

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
APPS_API_DIR = os.path.join(ROOT_DIR, "apps", "api")
if APPS_API_DIR not in sys.path:
    sys.path.insert(0, APPS_API_DIR)

from sqlalchemy import select
from app.config import settings
from app.db.session import session_factory
from app.models import User, AuditLog
from app.services.gmail_service import GmailService


async def exchange(email: str, code: str):
    print(f"\n🔐 Exchanging OAuth authorization code for candidate: {email}")

    async with session_factory() as db:
        user_res = await db.execute(select(User).where(User.email == email))
        user = user_res.scalar_one_or_none()

        if not user:
            print(f"❌ User with email '{email}' not found in database!")
            return False

        client_id = settings.google_client_id
        client_secret = settings.google_client_secret

        if user.google_tokens_encrypted:
            try:
                stored = json.loads(user.google_tokens_encrypted)
                if stored.get("client_id") and stored.get("client_secret"):
                    client_id = stored["client_id"]
                    client_secret = stored["client_secret"]
                    print(f"ℹ️ Using candidate's own Google OAuth Client ID: {client_id[:25]}...")
            except Exception:
                pass

        tokens = await GmailService.exchange_code_for_tokens(
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=settings.google_redirect_uri
        )

        if not tokens:
            print("❌ Token exchange failed. The code may be invalid, expired, or already used.")
            return False

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token:
            print("❌ No access_token received in response.")
            return False

        # Verify email with Gmail API
        gmail_address = await GmailService.get_user_email(access_token) or email
        print(f"✅ Successfully authenticated Gmail address: {gmail_address}")

        if not refresh_token:
            print("⚠️ Warning: Google did not return a new refresh_token.")
            print("  (Google only returns refresh_token on initial consent. Prompt=consent was used to ensure this.)")

        token_payload = json.dumps({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "gmail_address": gmail_address,
            "client_id": client_id,
            "client_secret": client_secret
        })

        user.google_tokens_encrypted = token_payload
        user.email = gmail_address
        db.add(user)
        db.add(AuditLog(
            action="GMAIL_OAUTH_TOKENS_STORED_MANUAL",
            entity_type="integration",
            user_id=user.id
        ))
        await db.commit()

        print("\n🎉 SUCCESS! OAuth tokens stored securely in database for:")
        print(f"   Candidate: {user.name} ({user.email})")
        print(f"   Has Refresh Token: {bool(refresh_token)}")
        print("   Auto-apply emails will now be sent directly from their own Gmail address!")
        return True


def main():
    parser = argparse.ArgumentParser(description="Exchange OAuth code for tokens")
    parser.add_argument("--url", help="Full redirect URL containing code and state", default=None)
    parser.add_argument("--email", help="Candidate email address", default=None)
    parser.add_argument("--code", help="Authorization code string", default=None)

    args = parser.parse_args()

    email = args.email
    code = args.code

    if args.url:
        parsed = urllib.parse.urlparse(args.url)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            code = params["code"][0]
        if "state" in params:
            email = urllib.parse.unquote(params["state"][0])

    if not code:
        print("❌ Error: You must provide either --url or --code.")
        sys.exit(1)

    if not email:
        email = "andrewchukwuka90@gmail.com"

    asyncio.run(exchange(email.strip(), code.strip()))


if __name__ == "__main__":
    main()

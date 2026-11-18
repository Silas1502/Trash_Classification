"""Prepare a private local token and ready-to-run SQL without printing credentials."""

import hashlib
import secrets
from pathlib import Path

from dotenv import dotenv_values, set_key


def main() -> None:
    backend = Path(__file__).resolve().parents[1]
    env_file = backend / ".env"
    token = dotenv_values(env_file).get("IMAGEKIT_CLEANUP_TOKEN") or secrets.token_urlsafe(48)
    if len(token) < 43:
        raise ValueError("Existing IMAGEKIT_CLEANUP_TOKEN is too short")
    sql = (backend / "sql" / "imagekit_cleanup.sql").read_text(encoding="utf-8")
    sql = sql.replace("__TOKEN_SHA256__", hashlib.sha256(token.encode()).hexdigest())
    output = backend.parent / ".venv" / "imagekit-cleanup-setup.sql"
    output.parent.mkdir(exist_ok=True)
    output.write_text(sql, encoding="utf-8")
    set_key(str(env_file), "IMAGEKIT_CLEANUP_TOKEN", token)
    print(f"SQL prepared: {output}")
    print("Backend token saved in backend/.env. No cloud configuration has been changed.")


if __name__ == "__main__":
    main()

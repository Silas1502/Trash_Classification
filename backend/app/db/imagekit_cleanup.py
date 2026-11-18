"""Consume durable Supabase deletion jobs without loading image bytes or the model."""

import asyncio
import logging

from app.db.imagekit_storage import ImageKitStorage
from app.db.supabase_db import SupabaseHistory

logger = logging.getLogger(__name__)


def process_next_cleanup(history: SupabaseHistory, storage: ImageKitStorage, token: str) -> bool:
    jobs = history.client.rpc("imagekit_cleanup_claim", {"p_token": token}).execute().data
    if not jobs:
        return False
    job = jobs[0]
    error = None
    try:
        storage.delete_prediction_images(job["prediction_id"], job["image_urls"])
    except Exception as exc:
        # Persist only exception type: provider messages may contain URLs or credentials.
        error = type(exc).__name__
        logger.warning("ImageKit cleanup job %s failed (%s); queued for retry", job["id"], error)
    history.client.rpc("imagekit_cleanup_finish", {
        "p_token": token, "p_id": job["id"], "p_lease": job["lease_token"], "p_error": error,
    }).execute()
    return True


async def watch_imagekit_cleanup(history: SupabaseHistory, storage: ImageKitStorage, token: str, interval: int) -> None:
    while True:
        try:
            # One claimed job at a time. Bound each sweep so other work gets time.
            for _ in range(10):
                if not await asyncio.to_thread(process_next_cleanup, history, storage, token):
                    break
                await asyncio.sleep(0)
        except Exception as exc:
            logger.warning("ImageKit cleanup unavailable (%s); will retry", type(exc).__name__)
        await asyncio.sleep(interval)

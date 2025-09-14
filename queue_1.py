# queue_1.py
import asyncio
import logging
from services.summarizer import summarize_note

logger = logging.getLogger(__name__)

# Kuyruk
QUEUE = asyncio.Queue()

async def worker_loop():
    logger.info("Worker loop started, waiting for jobs...")

    while True:
        note_id = await QUEUE.get()
        try:
            logger.info(f"[note_id={note_id}] Job received, starting summarization...")
            summarize_note(note_id)
            logger.info(f"[note_id={note_id}] Job finished.")
        except Exception as e:
            logger.exception(f"[note_id={note_id}] Worker error: {e}")
        finally:
            QUEUE.task_done()
            logger.info(f"[note_id={note_id}] Job marked as done in queue.")

def enqueue(note_id: int):
    QUEUE.put_nowait(note_id)
    logger.info(f"[note_id={note_id}] Job enqueued.")

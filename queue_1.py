import asyncio
import logging
from services.summarizer import summarize_note

# Logging ayarı
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def worker_loop(queue: asyncio.Queue):
    logging.info("[queue] Worker başlatıldı, görevler bekleniyor...")
    while True:
        note_id = await queue.get()
        try:
            logging.info(f"[queue] Note {note_id} işleme alındı.")
            summarize_note(note_id)
            logging.info(f"[queue] Note {note_id} işlendi ✅")
        except Exception as e:
            logging.error(f"[queue] Note {note_id} işlenirken hata: {e}")
        finally:
            queue.task_done()

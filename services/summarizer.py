# summarizer.py
from transformers import pipeline
import torch
from threading import Lock
from sqlmodel import Session
from db import engine
from models import Note
import logging

# Logging ayarları (app açılırken bir kez çağrılacak)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SUMMARIZER = None
summarize_lock = Lock()

def load_summarizer():
    global SUMMARIZER
    if SUMMARIZER is None:
        SUMMARIZER = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-6-6",
            device=0 if torch.cuda.is_available() else -1
        )
    return SUMMARIZER

def summarize_note(note_id: int):
    try:
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if not note or note.status == "done":
                logging.info(f"[summarizer] Note {note_id} bulunamadı veya zaten done.")
                return

            note.status = "processing"
            session.add(note)
            session.commit()
            logging.info(f"[summarizer] Note {note_id} -> processing")

            text = note.raw_text
            if len(text.split()) > 200:
                text = " ".join(text.split()[:200])
                logging.info(f"[summarizer] Note {note_id} text 200 kelimeye kısaltıldı.")

            with summarize_lock:
                summarizer = load_summarizer()
                result = summarizer(text, max_length=60, min_length=10, do_sample=False)

            note.summary = result[0]["summary_text"].strip()
            note.status = "done"
            session.add(note)
            session.commit()
            logging.info(f"[summarizer] Note {note_id} tamamlandı ✅")

    except Exception as e:
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if note:
                note.status = "failed"
                session.add(note)
                session.commit()
        logging.error(f"[summarizer] Hata Note {note_id}: {e}")

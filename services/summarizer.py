# services/summarizer.py
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
from threading import Lock
from sqlmodel import Session
from db import engine
from models import Note

# Global model ve lock
SUMMARIZER = None
summarize_lock = Lock()

def load_summarizer():
    global SUMMARIZER
    if SUMMARIZER is None:
        print("[LOG] Loading T5-small model...")
        tokenizer = T5Tokenizer.from_pretrained("t5-small")
        model = T5ForConditionalGeneration.from_pretrained("t5-small")
        device = 0 if torch.cuda.is_available() else -1
        SUMMARIZER = (tokenizer, model, device)
        print(f"[LOG] Model loaded. Device: {'cuda' if device>=0 else 'cpu'}")
    return SUMMARIZER

def summarize_note(note_id: int):
    # Thread-safe lock
    summarize_lock.acquire()
    try:
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if not note:
                print(f"[LOG] Note {note_id} not found")
                return
            # yeni satır
            if note.status == "done":
                print(f"[LOG] Note {note_id} already done")
                return

            note.status = "processing"
            session.add(note)
            session.commit()
            print(f"[LOG] Note {note_id} set to processing")

            # Text’i kısalt (200 kelime)
            text = note.raw_text
            if len(text.split()) > 200:
                text = " ".join(text.split()[:200])

            tokenizer, model, device = load_summarizer()
            input_text = "summarize: " + text
            input_ids = tokenizer(input_text, return_tensors="pt").input_ids

            if device >= 0:
                input_ids = input_ids.to(f"cuda:{device}")
                model = model.to(f"cuda:{device}")
            else:
                model = model.to("cpu")

            # Generate summary
            outputs = model.generate(
                input_ids,
                max_length=40,
                min_length=10,
                num_beams=2,
                early_stopping=True
            )
            summary_result = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # DB update
            note.summary = summary_result.strip()
            note.status = "done"
            session.add(note)
            session.commit()
            print(f"[LOG] Note {note_id} done")
    except Exception as e:
        print(f"[LOG] Note {note_id} failed: {e}")
        # Eğer fail olursa ayrı session ile failed ata
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if note:
                note.status = "failed"
                session.add(note)
                session.commit()
    finally:
        summarize_lock.release()

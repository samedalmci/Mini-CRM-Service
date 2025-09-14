# summarizer_optimized.py
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
        tokenizer = T5Tokenizer.from_pretrained("t5-small")
        model = T5ForConditionalGeneration.from_pretrained("t5-small")
        device = 0 if torch.cuda.is_available() else -1
        SUMMARIZER = (tokenizer, model, device)
    return SUMMARIZER

def summarize_note(note_id: int):
    # Yeni session aç
    with Session(engine) as session:
        note = session.get(Note, note_id)
        if not note or note.status in ("done", "processing"):
            return

        # Önce status'u commit et
        note.status = "processing"
        session.add(note)
        session.commit()

    try:
        # Kısa text kullan (200 kelime)
        text = note.raw_text
        if len(text.split()) > 200:
            text = " ".join(text.split()[:200])

        with summarize_lock:
            tokenizer, model, device = load_summarizer()
            input_text = "summarize: " + text
            input_ids = tokenizer(input_text, return_tensors="pt").input_ids

            if device >= 0:
                input_ids = input_ids.to(f"cuda:{device}")
                model = model.to(f"cuda:{device}")
            else:
                model = model.to("cpu")

            outputs = model.generate(
                input_ids,
                max_length=40,      # CPU dostu
                min_length=10,
                num_beams=2,        # CPU dostu
                early_stopping=True
            )
            summary_result = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Sonucu DB'ye kaydet
        with Session(engine) as session:
            note = session.get(Note, note_id)
            note.summary = summary_result.strip()
            note.status = "done"
            session.add(note)
            session.commit()

    except Exception as e:
        print("Summarization error:", e)
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if note:
                note.status = "failed"
                session.add(note)
                session.commit()

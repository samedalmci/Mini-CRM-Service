# summarizer.py
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
from threading import Lock
from sqlmodel import Session
from db import engine
from models import Note

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
    try:
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if not note or note.status == "done":
                return

            note.status = "processing"
            session.add(note)
            session.commit()

            text = note.raw_text
            if len(text.split()) > 200:
                text = " ".join(text.split()[:200])

            with summarize_lock:
                tokenizer, model, device = load_summarizer()
                print("Summarizer loaded:", model)

                # T5 için input
                input_text = "summarize: " + text
                input_ids = tokenizer(input_text, return_tensors="pt").input_ids
                if device >= 0:
                    input_ids = input_ids.to(f"cuda:{device}")
                    model = model.to(f"cuda:{device}")

                # Generate summary
                outputs = model.generate(
                    input_ids,
                    max_length=60,
                    min_length=10,
                    num_beams=4,
                    early_stopping=True
                )
                result = tokenizer.decode(outputs[0], skip_special_tokens=True)
                print("Summarization result:", result)

            note.summary = result.strip()
            note.status = "done"
            session.add(note)
            session.commit()

    except Exception as e:
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if note:
                note.status = "failed"
                session.add(note)
                session.commit()
        print("Summarization error:", e)

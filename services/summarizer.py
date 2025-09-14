# services/summarizer.py
from transformers import PegasusTokenizer, PegasusForConditionalGeneration
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
        print("[LOG] Loading Pegasus model...")
        model_name = "google/pegasus-xsum" # Veya 'google/pegasus-xsum-c4-small'
        tokenizer = PegasusTokenizer.from_pretrained(model_name)
        model = PegasusForConditionalGeneration.from_pretrained(model_name)
        
        # Quantization denemesi (512MB için çok önemli)
        # model = model.half().to("cuda") # 16-bit float
        
        device = 0 if torch.cuda.is_available() else -1
        SUMMARIZER = (tokenizer, model, device)
        print(f"[LOG] Model loaded. Device: {'cuda' if device>=0 else 'cpu'}")
    return SUMMARIZER

def summarize_note(note_id: int):
    summarize_lock.acquire()
    try:
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if not note:
                print(f"[LOG] Note {note_id} not found")
                return
            
            if note.status == "done":
                print(f"[LOG] Note {note_id} already done")
                return

            note.status = "processing"
            session.add(note)
            session.commit()
            print(f"[LOG] Note {note_id} set to processing")

            text = note.raw_text
            # Metni kısa tutmak önemli
            if len(text.split()) > 200:
                text = " ".join(text.split()[:200])

            tokenizer, model, device = load_summarizer()
            
            # Pegasus için farklı bir input formatı
            input_text = text
            input_ids = tokenizer(input_text, return_tensors="pt", truncation=True).input_ids

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
        with Session(engine) as session:
            note = session.get(Note, note_id)
            if note:
                note.status = "failed"
                session.add(note)
                session.commit()
    finally:
        summarize_lock.release()
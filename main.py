# main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

# ---------- Database Setup ----------
DATABASE_URL = "sqlite:///./notes.db"  # Ücretsiz/test için SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class NoteModel(Base):
    __tablename__ = "note"
    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ---------- FastAPI Setup ----------
app = FastAPI(title="Lightweight Summarizer")

# ---------- Load Model Once ----------
@app.on_event("startup")
def load_model():
    global tokenizer, model
    print("Loading T5-small model...")
    tokenizer = T5Tokenizer.from_pretrained("t5-small")
    model = T5ForConditionalGeneration.from_pretrained("t5-small")
    model.eval()  # inference modu
    print("Model loaded!")

# ---------- Request Body ----------
class Note(BaseModel):
    text: str

# ---------- Background Summarization ----------
def summarize_note(note_id: int):
    db = SessionLocal()
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not note:
        db.close()
        return

    try:
        # Status: processing
        note.status = "processing"
        db.commit()

        # T5-small özetleme
        inputs = tokenizer.encode("summarize: " + note.raw_text, return_tensors="pt", max_length=512, truncation=True)
        summary_ids = model.generate(
            inputs,
            max_length=150,
            min_length=30,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        # Veritabanına kaydet
        note.summary = summary
        note.status = "done"
        note.updated_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        note.status = "failed"
        db.commit()
        print("Error:", e)
    finally:
        db.close()

# ---------- API Endpoints ----------
@app.post("/notes/")
async def add_note(note: Note, background_tasks: BackgroundTasks):
    db = SessionLocal()
    db_note = NoteModel(raw_text=note.text, status="queued")
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    db.close()

    # Background thread ile özetle
    background_tasks.add_task(summarize_note, db_note.id)
    return {"status": "queued", "note_id": db_note.id}

@app.get("/notes/{note_id}")
def get_note(note_id: int):
    db = SessionLocal()
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    db.close()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {
        "id": note.id,
        "raw_text": note.raw_text,
        "summary": note.summary,
        "status": note.status,
        "created_at": note.created_at,
        "updated_at": note.updated_at
    }

@app.get("/notes/")
def list_notes():
    db = SessionLocal()
    notes = db.query(NoteModel).all()
    db.close()
    return [
        {
            "id": note.id,
            "raw_text": note.raw_text,
            "summary": note.summary,
            "status": note.status,
            "created_at": note.created_at,
            "updated_at": note.updated_at
        } for note in notes
    ]

# ---------- Run Server ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

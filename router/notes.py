# # routes/notes.py
# from fastapi import APIRouter, Depends
# from sqlmodel import Session, select
# from db import get_session
# from models import Note, User
# from auth import get_current_active_user
# from pydantic import BaseModel
# from queue_1 import add_to_queue

# router = APIRouter()

# class NoteCreate(BaseModel):
#     raw_text: str

# @router.get("/notes/")
# async def list_notes(current_user: User  = Depends(get_current_active_user),
#                      session: Session = Depends(get_session)):

#     if current_user.role == "ADMIN":
#         statement = select(Note)
#     else:
#         statement = select(Note).where(Note.user_id == current_user.id)

#     notes = session.exec(statement).all()

#     return [
#         {
#             "id": note.id,
#             "raw_text": note.raw_text,
#             "summary": note.summary,
#             "status": note.status,
#             "user_id": note.user_id,
#             "created_at": note.created_at,
#             "updated_at": note.updated_at
#         }
#         for note in notes
#     ]

# @router.post("/notes/")
# async def create_note(note_in: NoteCreate,
#                       current_user: User = Depends(get_current_active_user),
#                       session: Session = Depends(get_session)):

#     new_note = Note(
#         raw_text=note_in.raw_text,
#         user_id=current_user.id,
#         status="queued"
#     )
#     session.add(new_note)
#     session.commit()
#     session.refresh(new_note)

#     # Queue ile job ekle
#     add_to_queue(new_note.id)

#     return {
#         "id": new_note.id,
#         "raw_text": new_note.raw_text,
#         "status": new_note.status,
#         "user_id": new_note.user_id
#     }

from fastapi import FastAPI
import asyncio
from threading import Thread
from router import users, notes
from db import create_db_and_tables
from queue_1 import worker_loop
from services.summarizer import summarize_note


app = FastAPI()

app.include_router(users.router)
app.include_router(notes.router)

@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    # Veritabanı bağlantısını bloklamadan başlat
    asyncio.create_task(init_db())
    # Worker thread'i başlat
    Thread(target=worker_loop, args=(summarize_note,), daemon=True).start()

async def init_db():
    from db import engine
    with engine.begin() as conn:
        pass



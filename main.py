from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Veritabanı bağlantısını bloklayıcı değil, background task olarak aç
    asyncio.create_task(init_db())

async def init_db():
    from db import engine
    # Burada connect edip tabloları kontrol edersin
    with engine.begin() as conn:
        pass

# db.py
from sqlmodel import SQLModel, create_engine, Session
import os

# Docker'dan gelen DATABASE_URL'i al, yoksa local kullan
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb")

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
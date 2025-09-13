from fastapi import FastAPI
from db import create_db_and_tables
from router  import users, notes

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(users.router)
app.include_router(notes.router)











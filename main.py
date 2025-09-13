from db import create_db_and_tables

@app.on_event("startup")
def on_startup():
    create_db_and_tables()  # sync olarak çağırmak yeterli

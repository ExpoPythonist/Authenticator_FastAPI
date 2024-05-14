from fastapi import FastAPI

import models
from api.auth import auth_router
from config.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/')
async def status_check():
    return {"status": True}


app.include_router(auth_router)
